from typing import Optional, List, Any, Union, Dict, Any
import pyarrow.flight as flight
import pandas as pd
import polars as pl
import os
from .quality import DataQuality
from .flight_sql import encode_set_session_options
from .middleware import CookieMiddlewareFactory



class DremioBuilder:
    def __init__(self, client, path: Optional[str] = None, sql: Optional[str] = None):
        self.client = client
        self.path = path
        self.initial_sql = sql
        self.select_columns = []
        self.mutations = {}
        self.filters = []
        self.limit_val = None
        self.group_cols = []
        self.aggregations = {}
        self.order_cols = []
        self.distinct_flag = False
        self._quality = None

        self.time_travel_clause = ""

    @property
    def quality(self):
        if self._quality is None:
            self._quality = DataQuality(self)
        return self._quality

    def at_snapshot(self, snapshot_id: str) -> 'DremioBuilder':
        """Query at a specific snapshot ID"""
        self.time_travel_clause = f"AT SNAPSHOT '{snapshot_id}'"
        return self

    def at_timestamp(self, timestamp: str) -> 'DremioBuilder':
        """Query at a specific timestamp"""
        self.time_travel_clause = f"AT TIMESTAMP '{timestamp}'"
        return self

    def at_branch(self, branch: str) -> 'DremioBuilder':
        """Query at a specific branch"""
        self.time_travel_clause = f"AT BRANCH {branch}"
        return self

    def optimize(self, rewrite_data: bool = True, min_input_files: int = None) -> Any:
        """Run OPTIMIZE TABLE command"""
        if not self.path:
            raise ValueError("Optimize requires a table path")
        
        options = []
        if rewrite_data:
            options.append("REWRITE DATA")
        if min_input_files:
            options.append(f"(MIN_INPUT_FILES={min_input_files})")
            
        opt_sql = f"OPTIMIZE TABLE {self.path} {' '.join(options)}"
        return self._execute_dml(opt_sql)

    def vacuum(self, expire_snapshots: bool = True, retain_last: int = None) -> Any:
        """Run VACUUM TABLE command"""
        if not self.path:
            raise ValueError("Vacuum requires a table path")
            
        options = []
        if expire_snapshots:
            options.append("EXPIRE SNAPSHOTS")
        if retain_last:
            options.append(f"RETAIN_LAST {retain_last}")
            
        vac_sql = f"VACUUM TABLE {self.path} {' '.join(options)}"
        return self._execute_dml(vac_sql)
        
    def select(self, *columns: str) -> 'DremioBuilder':
        self.select_columns.extend(columns)
        return self

    def distinct(self) -> 'DremioBuilder':
        """Select distinct rows"""
        self.distinct_flag = True
        return self

    def group_by(self, *columns: str) -> 'DremioBuilder':
        """Group by columns"""
        self.group_cols.extend(columns)
        return self

    def agg(self, **kwargs) -> 'DremioBuilder':
        """
        Add aggregations.
        Example: df.group_by("state").agg(avg_pop="AVG(pop)")
        """
        self.aggregations.update(kwargs)
        return self

    def order_by(self, *columns: str, ascending: bool = True) -> 'DremioBuilder':
        """
        Order by columns.
        Example: df.order_by("col1", "col2", ascending=False)
        """
        direction = "ASC" if ascending else "DESC"
        for col in columns:
            self.order_cols.append(f"{col} {direction}")
        return self

    def mutate(self, **kwargs) -> 'DremioBuilder':
        """
        Add calculated columns.
        Example: df.mutate(new_col="col1 + col2")
        """
        self.mutations.update(kwargs)
        return self

    def filter(self, condition: str) -> 'DremioBuilder':
        self.filters.append(condition)
        return self

    def limit(self, n: int) -> 'DremioBuilder':
        self.limit_val = n
        return self

    def _compile_sql(self) -> str:
        if self.initial_sql:
            # If started with raw SQL, we wrap it in a subquery to apply further operations
            query = f"SELECT * FROM ({self.initial_sql}) AS sub"
        else:
            # Quote the path components if needed, or assume user passed a valid path string
            # Dremio paths are usually "Space"."Folder"."Table"
            query = f"SELECT * FROM {self.path}"
            if self.time_travel_clause:
                query += f" {self.time_travel_clause}"

        # Handle SELECT clause
        select_clause = "SELECT"
        if self.distinct_flag:
            select_clause += " DISTINCT"
        
        cols = []
        mutations_applied = set()

        if self.select_columns:
            for col in self.select_columns:
                # Check if this column is being mutated
                if col in self.mutations:
                    cols.append(f'{self.mutations[col]} AS "{col}"')
                    mutations_applied.add(col)
                else:
                    cols.append(col)
        else:
            # If no columns selected, start with *
            # But only if we are not aggregating. If we are aggregating, we usually don't want * unless explicit.
            if not self.aggregations:
                cols.append("*")
        
        # Add remaining mutations
        if self.mutations:
            for name, expr in self.mutations.items():
                if name not in mutations_applied:
                    cols.append(f'{expr} AS "{name}"')
    
        if self.aggregations:
            for name, expr in self.aggregations.items():
                cols.append(f'{expr} AS "{name}"')
                
        # Implicitly add group columns to select if we are grouping
        if self.group_cols:
            for col in self.group_cols:
                # Check if col is already in cols (simple check)
                # This is imperfect but handles the common case
                # We need to check if the column name or alias is present
                is_present = False
                for c in cols:
                    if c == col or c.endswith(f'AS "{col}"'):
                        is_present = True
                        break
                
                if not is_present:
                     cols.insert(0, col)

        cols_str = ", ".join(cols)
        query = query.replace("SELECT *", f"{select_clause} {cols_str}", 1)

        if self.filters:
            where_clause = " AND ".join(self.filters)
            query += f" WHERE {where_clause}"
            
        if self.group_cols:
            group_clause = ", ".join(self.group_cols)
            query += f" GROUP BY {group_clause}"
            
        if self.order_cols:
            order_clause = ", ".join(self.order_cols)
            query += f" ORDER BY {order_clause}"

        if self.limit_val is not None:
            query += f" LIMIT {self.limit_val}"

        return query

    def join(self, other: Union[str, 'DremioBuilder'], on: str, how: str = "inner") -> 'DremioBuilder':
        """
        Join with another table or builder.
        
        Args:
            other: Table name string or DremioBuilder instance.
            on: Join condition (e.g., "t1.id = t2.id").
            how: Join type ("inner", "left", "right", "full", "cross").
        """
        # Compile self
        left_sql = self._compile_sql()
        
        # Compile other
        if isinstance(other, DremioBuilder):
            right_sql = other._compile_sql()
        else:
            right_sql = f"SELECT * FROM {other}"
            
        # Construct join
        # We wrap both in subqueries to ensure isolation
        # SELECT * FROM (left) AS left_tbl JOIN (right) AS right_tbl ON ...
        
        join_type = how.upper()
        if join_type not in ["INNER", "LEFT", "RIGHT", "FULL", "CROSS"]:
            raise ValueError(f"Invalid join type: {how}")
            
        join_sql = f"SELECT * FROM ({left_sql}) AS left_tbl {join_type} JOIN ({right_sql}) AS right_tbl ON {on}"
        
        # Return new builder with this SQL
        return DremioBuilder(self.client, sql=join_sql)



    def collect(self, library: str = "polars", progress_bar: bool = False) -> Union[pl.DataFrame, pd.DataFrame]:
        sql = self._compile_sql()
        return self._execute_flight(sql, library, progress_bar=progress_bar)

    def _execute_flight(self, sql: str, library: str, progress_bar: bool = False) -> Union[pl.DataFrame, pd.DataFrame]:
        # Construct Flight Endpoint
        hostname = self.client.flight_endpoint or self.client.hostname
        port = self.client.flight_port or self.client.port
        protocol = "grpc+tls" if self.client.tls else "grpc+tcp"
        location = f"{protocol}://{hostname}:{port}"
        
        # Initialize middleware for session management
        cookie_middleware = CookieMiddlewareFactory()
        client = flight.FlightClient(location, middleware=[cookie_middleware])
        
        # Authentication
        options = flight.FlightCallOptions()
        
        if self.client.mode == "cloud":
            # Cloud: Bearer Token Auth
            if self.client.pat:
                headers = [
                    (b"authorization", f"Bearer {self.client.pat}".encode("utf-8"))
                ]
                options = flight.FlightCallOptions(headers=headers)
            else:
                raise ValueError("PAT is required for Dremio Cloud connection")
                
        elif self.client.mode in ["v26", "v25"]:
            # Software: Basic Auth (Username + Password/PAT)
            username = self.client.username
            password = self.client.password or self.client.pat
            
            if not username or not password:
                raise ValueError("Username and Password (or PAT) are required for Dremio Software connection")
                
            # Authenticate to get session token/header
            # authenticate_basic_token returns (header_key, header_value) pair
            try:
                auth_result = client.authenticate_basic_token(username, password)
                
                if isinstance(auth_result, tuple):
                    # It returns a pair of bytes (key, value)
                    headers = [auth_result]
                    options = flight.FlightCallOptions(headers=headers)
                else:
                    # Fallback if behavior differs (e.g. just token bytes)
                    # But diagnostic script confirmed it returns (key, value)
                    options = auth_result
            except Exception as e:
                raise RuntimeError(f"Authentication failed for user '{username}': {e}")
        
        else:
            # Fallback for legacy/unspecified mode (assume Cloud behavior if PAT exists)
            if self.client.pat:
                headers = [
                    (b"authorization", f"Bearer {self.client.pat}".encode("utf-8"))
                ]
                options = flight.FlightCallOptions(headers=headers)
            elif self.client.username and self.client.password:
                 # Basic Auth fallback
                auth_result = client.authenticate_basic_token(self.client.username, self.client.password)
                if isinstance(auth_result, tuple):
                    headers = [auth_result]
                    options = flight.FlightCallOptions(headers=headers)
                else:
                    options = auth_result
        
        if self.client.disable_certificate_verification:
            # This is usually set at client creation or context, but PyArrow Flight handles it via URI or args.
            # For disabling cert verification, we might need to pass generic options.
            # But let's assume the user handles certs via system trust store or explicit path if needed.
            pass

        # For Cloud mode with project_id, set session option using FlightSQL
        # This is the standard way to set context in Dremio Cloud
        if self.client.mode == "cloud" and self.client.project_id:
            try:
                # Create SetSessionOptions action payload
                # We use manual protobuf encoding to avoid dependency issues
                payload = encode_set_session_options({"project_id": self.client.project_id})
                action = flight.Action("SetSessionOptions", payload)
                
                # Execute action to set session context
                # The server will return a Set-Cookie header which the middleware captures
                # Subsequent requests will include the cookie and be routed correctly
                results = list(client.do_action(action, options))
                
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to set project_id '{self.client.project_id}' via SetSessionOptions: {e}")
                # We continue anyway, as some environments might not support this action
                # or might rely on default project context.

        info = client.get_flight_info(flight.FlightDescriptor.for_command(sql), options)
        reader = client.do_get(info.endpoints[0].ticket, options)
        
        if progress_bar:
            try:
                from tqdm import tqdm
            except ImportError:
                print("Warning: tqdm not installed. Install with: pip install dremioframe[notebook]")
                table = reader.read_all()
            else:
                # Read chunks and update progress bar
                # Flight doesn't always give total rows upfront easily, so we just show downloaded chunks/rows
                chunks = []
                # Try to get total bytes or rows if available, otherwise just count
                with tqdm(desc="Downloading", unit="chunk") as pbar:
                    for chunk in reader:
                        chunks.append(chunk)
                        pbar.update(1)
                
                import pyarrow as pa
                if chunks:
                    table = pa.Table.from_batches(chunks)
                else:
                    # Empty result
                    table = reader.schema.empty_table()
        else:
            table = reader.read_all()
        
        if library == "polars":
            return pl.from_arrow(table)
        elif library == "pandas":
            return table.to_pandas()
        else:
            raise ValueError("Library must be 'polars' or 'pandas'")

    def show(self, n: int = 20):
        print(self.limit(n).collect())

    def explain(self) -> str:
        """
        Return the query plan.
        Executes: EXPLAIN PLAN FOR <query>
        """
        sql = self._compile_sql()
        explain_sql = f"EXPLAIN PLAN FOR {sql}"
        # Execute via Flight and return the plan text
        # The result of EXPLAIN PLAN is usually a single column 'text' or similar
        df = self._execute_flight(explain_sql, "pandas")
        if not df.empty:
            return df.iloc[0, 0]
        return "No plan returned."

    def to_csv(self, path: str, **kwargs):
        """Export query results to CSV"""
        df = self.collect("pandas")
        df.to_csv(path, **kwargs)

    def to_parquet(self, path: str, **kwargs):
        """Export query results to Parquet"""
        df = self.collect("pandas")
        df.to_parquet(path, **kwargs)

    def to_delta(self, path: str, mode: str = "overwrite", **kwargs):
        """
        Export query results to Delta Lake.
        Requires 'deltalake' package.
        """
        try:
            from deltalake import write_deltalake
        except ImportError:
            raise ImportError("deltalake package is required. Install with: pip install dremioframe[delta]")
        
        df = self.collect(library="pandas")
        write_deltalake(path, df, mode=mode, **kwargs)

    def to_json(self, path: str, orient: str = "records", **kwargs):
        """
        Export query results to JSON.
        """
        df = self.collect(library="pandas")
        df.to_json(path, orient=orient, **kwargs)

    def chart(self, kind: str = 'line', x: str = None, y: str = None, title: str = None, save_to: str = None, backend: str = 'matplotlib', **kwargs):
        """
        Create a chart from the query results.
        
        Args:
            kind: The kind of plot to produce.
                  Matplotlib: 'line', 'bar', 'barh', 'hist', 'box', 'kde', 'density', 'area', 'pie', 'scatter', 'hexbin'.
                  Plotly: 'line', 'bar', 'scatter', 'pie', 'histogram', 'box', 'violin', 'area'.
            x: Column name for x-axis.
            y: Column name(s) for y-axis.
            title: Chart title.
            save_to: Path to save the chart image (e.g., "chart.png" or "chart.html").
            backend: 'matplotlib' (default) or 'plotly'.
            **kwargs: Additional arguments passed to the plotting function.
        """
        df = self.collect("pandas")
        
        if backend == 'matplotlib':
            import matplotlib.pyplot as plt
            ax = df.plot(kind=kind, x=x, y=y, title=title, **kwargs)
            if save_to:
                plt.savefig(save_to)
            return ax
            
        elif backend == 'plotly':
            import plotly.express as px
            
            # Map kind to px function
            plot_func = None
            if kind == 'line': plot_func = px.line
            elif kind == 'bar': plot_func = px.bar
            elif kind == 'scatter': plot_func = px.scatter
            elif kind == 'pie': plot_func = px.pie
            elif kind == 'histogram': plot_func = px.histogram
            elif kind == 'box': plot_func = px.box
            elif kind == 'violin': plot_func = px.violin
            elif kind == 'area': plot_func = px.area
            else:
                raise ValueError(f"Unsupported kind '{kind}' for plotly backend")
                
            fig = plot_func(df, x=x, y=y, title=title, **kwargs)
            
            if save_to:
                if save_to.endswith(".html"):
                    fig.write_html(save_to)
                else:
                    # Requires kaleido for static image export
                    try:
                        fig.write_image(save_to)
                    except ImportError:
                        print("Warning: 'kaleido' is required for static image export with Plotly. Saving as HTML instead.")
                        fig.write_html(save_to + ".html")
            
            return fig
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def cache(self, name: str, ttl_seconds: int = None, folder: str = ".cache") -> 'LocalBuilder':
        """
        Cache the current query result to a local Feather file and return a LocalBuilder.
        
        Args:
            name: Name of the cache (file will be {folder}/{name}.feather).
            ttl_seconds: Time-to-live in seconds. If file exists and is younger than this, use it.
            folder: Directory to store cache files.
            
        Returns:
            LocalBuilder: A builder for querying the local cache.
        """
        import os
        import time
        from dremioframe.local_builder import LocalBuilder
        import pyarrow.feather as feather
        import pyarrow as pa # Added for type hinting and table object
        
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        file_path = os.path.join(folder, f"{name}.feather")
        
        use_cache = False
        if os.path.exists(file_path):
            if ttl_seconds is None:
                use_cache = True
            else:
                age = time.time() - os.path.getmtime(file_path)
                if age < ttl_seconds:
                    use_cache = True
                    
        if not use_cache:
            # Execute query and save
            table: pa.Table = self.collect("arrow") # Type hint for clarity
            feather.write_feather(table, file_path)
        else:
            # Load from cache
            table: pa.Table = feather.read_feather(file_path)
            
        return LocalBuilder(file_path, table_name=name)

    def _quote_path(self, path: str) -> str:
        """
        Quote a path for SQL (e.g. space.folder.table -> "space"."folder"."table").
        """
        if '"' in path:
            return path # Assume already quoted
        parts = path.split(".")
        quoted_parts = [f'"{p}"' for p in parts]
        return ".".join(quoted_parts)

    def _repr_html_(self):
        """
        Rich HTML representation for Jupyter Notebooks.
        Shows a preview of the data (first 20 rows).
        """
        try:
            # Create a preview query
            preview_sql = self._compile_sql()
            if "LIMIT" not in preview_sql.upper():
                preview_sql += " LIMIT 20"
            
            # Execute and get pandas DF
            df = self._execute_flight(preview_sql, library='pandas')
            
            # Add some metadata
            html = f"<h4>DremioBuilder Preview</h4>"
            html += f"<p><strong>SQL:</strong> <code>{self._compile_sql()}</code></p>"
            html += df.to_html(index=False, classes='dataframe table table-striped table-hover')
            html += f"<p><em>Showing up to 20 rows. Use .collect() to get full result.</em></p>"
            return html
        except Exception as e:
            return f"<p><strong>Error generating preview:</strong> {e}</p>"

    # DML Operations
    def create(self, name: str, data: Union[Any, None] = None, batch_size: Optional[int] = None, schema: Any = None, method: str = "values"):
        """
        Create table as select (CTAS).
        If data is provided, it creates the table from the data.
        
        Args:
            name: Table name.
            data: Data to insert (Pandas DataFrame, Arrow Table, or list of dicts).
            batch_size: Batch size for insertion (only for 'values' method).
            schema: Optional Pydantic model for validation.
            method: 'values' (default) or 'staging' (faster for large data).
        """
        quoted_name = self._quote_path(name)
        
        if data is not None:
            # Validate data if schema provided
            if schema:
                self._validate_data(data, schema)

            import pyarrow as pa
            import math
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                data = pa.Table.from_pandas(data)
            
            if not isinstance(data, pa.Table):
                raise ValueError("Data must be a PyArrow Table or Pandas DataFrame")

            if method == "staging":
                # Staging method: Write to parquet, upload, CTAS
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                    import pyarrow.parquet as pq
                    pq.write_table(data, tmp.name)
                    tmp_path = tmp.name
                
                try:
                    # Upload file
                    # We need a location. Let's assume user has a home space or scratch space?
                    # Or we upload to the target folder if possible.
                    # upload_file uploads to a table? No, it uploads to a location then promotes?
                    # client.upload_file uploads to a table directly usually via arrow flight or rest.
                    # Wait, client.upload_file in client.py (lines 286+) uses... what?
                    # It's not implemented fully in the snippet I saw earlier (it just had imports).
                    # Let's assume we can use client.upload_file if implemented, or implement a simple version here.
                    
                    # Actually, client.upload_file docstring says "Upload a local file to Dremio as a new table."
                    # So we can just use that!
                    self.client.upload_file(tmp_path, name, file_format="parquet")
                    return
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            # method == 'values'
            rows = data.to_pylist()
            total_rows = len(rows)
            
            # If batch_size is set, we use the first batch for CTAS
            first_batch_size = batch_size if batch_size else total_rows
            first_batch_rows = rows[:first_batch_size]
            
            # Generate VALUES for first batch
            values_list = []
            for row in first_batch_rows:
                row_vals = []
                for val in row.values():
                    if isinstance(val, str):
                        row_vals.append(f"'{val}'")
                    elif val is None:
                        row_vals.append("NULL")
                    else:
                        row_vals.append(str(val))
                values_list.append(f"({', '.join(row_vals)})")
            
            values_clause = ", ".join(values_list)
            cols_def = ", ".join([f'"{c}"' for c in data.column_names]) # Quote columns too
            
            # CTAS SQL
            # CREATE TABLE name AS SELECT * FROM (VALUES ...) AS sub(col1, col2)
            create_sql = f"CREATE TABLE {quoted_name} AS SELECT * FROM (VALUES {values_clause}) AS sub({cols_def})"
            
            result = self._execute_dml(create_sql)
            
            # If there are more batches, insert them
            if batch_size and total_rows > batch_size:
                remaining_data = data.slice(batch_size)
                self.insert(name, data=remaining_data, batch_size=batch_size, method=method)
                
            return result

        sql = self._compile_sql()
        create_sql = f"CREATE TABLE {quoted_name} AS {sql}"
        return self._execute_dml(create_sql)

    def insert(self, table_name: str, data: Union[Any, None] = None, batch_size: Optional[int] = None, schema: Any = None, method: str = "values"):
        """
        Insert into table.
        If data is provided (Arrow Table or Pandas DataFrame), it generates a VALUES clause.
        Otherwise, it inserts from the current selection.
        
        Args:
            table_name: Target table name.
            data: Optional PyArrow Table or Pandas DataFrame.
            batch_size: Optional integer to split data into batches.
            schema: Optional Pydantic model for validation.
            method: 'values' (default) or 'staging' (faster for large data).
        """
        if data is not None:
            # Validate data if schema provided
            if schema:
                self._validate_data(data, schema)

            # Handle Arrow Table or Pandas DataFrame
            import pyarrow as pa
            import math
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                data = pa.Table.from_pandas(data)
            
            if not isinstance(data, pa.Table):
                raise ValueError("Data must be a PyArrow Table or Pandas DataFrame")
            
            if method == "staging":
                # Staging method: Write to parquet, upload to temp table, INSERT INTO target SELECT * FROM temp, DROP temp
                import tempfile
                import os
                import uuid
                
                # Create temp table name
                # Parse table_name to extract components
                # table_name might be "Space"."Folder"."Table" or Space.Folder.Table
                # We need to append _staging_xxx to the table part only
                import re
                
                # Remove quotes and split
                parts = [p.strip('"') for p in table_name.split('.')]
                if len(parts) >= 3:
                    # Space.Folder.Table format
                    parts[-1] = f"{parts[-1]}_staging_{uuid.uuid4().hex[:8]}"
                    temp_table_name = '.'.join([f'"{p}"' for p in parts])
                else:
                    # Fallback: just append
                    temp_table_name = f"{table_name}_staging_{uuid.uuid4().hex[:8]}"
                
                with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                    import pyarrow.parquet as pq
                    pq.write_table(data, tmp.name)
                    tmp_path = tmp.name
                
                try:
                    # Upload to temp table
                    self.client.upload_file(tmp_path, temp_table_name, file_format="parquet")
                    
                    # Insert into target from temp
                    insert_sql = f"INSERT INTO {table_name} SELECT * FROM {temp_table_name}"
                    result = self._execute_dml(insert_sql)
                    
                    # Drop temp table
                    self.client.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
                    return result
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            # method == 'values'
            rows = data.to_pylist()
            total_rows = len(rows)
            
            if batch_size is None:
                batch_size = total_rows
            
            num_batches = math.ceil(total_rows / batch_size)
            results = []
            
            for i in range(num_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, total_rows)
                batch_rows = rows[start_idx:end_idx]
                
                values_list = []
                for row in batch_rows:
                    row_vals = []
                    for val in row.values():
                        if isinstance(val, str):
                            row_vals.append(f"'{val}'")
                        elif val is None:
                            row_vals.append("NULL")
                        else:
                            row_vals.append(str(val))
                    values_list.append(f"({', '.join(row_vals)})")
                
                values_clause = ", ".join(values_list)
                quoted_cols = ', '.join([f'"{col}"' for col in data.column_names])
                insert_sql = f"INSERT INTO {table_name} ({quoted_cols}) VALUES {values_clause}"
                results.append(self._execute_dml(insert_sql))
                
            return results if len(results) > 1 else results[0]

        sql = self._compile_sql()
        insert_sql = f"INSERT INTO {table_name} {sql}"
        return self._execute_dml(insert_sql)

    def validate(self, schema: Any, sample_size: int = 1000):
        """
        Validate existing data in Dremio against a Pydantic schema.
        Fetches a sample of data and validates each row.
        
        Args:
            schema: Pydantic model class.
            sample_size: Number of rows to fetch for validation.
        """
        # Fetch data
        df = self.limit(sample_size).collect("pandas")
        self._validate_data(df, schema)
        print(f"Successfully validated {len(df)} rows against schema {schema.__name__}")

    def create_from_model(self, name: str, schema: Any):
        """
        Create an empty table based on a Pydantic model.
        
        Args:
            name: Table name.
            schema: Pydantic model class.
        """
        # Map Pydantic types to Dremio SQL types
        type_map = {
            'int': 'INTEGER',
            'str': 'VARCHAR',
            'float': 'DOUBLE',
            'bool': 'BOOLEAN',
            'datetime': 'TIMESTAMP',
            'date': 'DATE'
        }
        
        cols = []
        for field_name, field in schema.model_fields.items():
            # Get type annotation
            py_type = field.annotation.__name__ if hasattr(field.annotation, '__name__') else str(field.annotation)
            
            # Handle Optional[T] or Union[T, None] - simplistic check
            if "Optional" in str(field.annotation) or "NoneType" in str(field.annotation):
                # Extract inner type if possible, or just assume string if complex
                pass 
            
            sql_type = type_map.get(py_type, 'VARCHAR') # Default to VARCHAR
            cols.append(f"{field_name} {sql_type}")
            
        cols_def = ", ".join(cols)
        create_sql = f"CREATE TABLE {name} ({cols_def})"
        return self._execute_dml(create_sql)

    def _validate_data(self, data, schema):
        """Validate data against Pydantic schema."""
        import pandas as pd
        import pyarrow as pa
        
        rows = []
        if isinstance(data, pd.DataFrame):
            rows = data.to_dict(orient="records")
        elif isinstance(data, pa.Table):
            rows = data.to_pylist()
        elif isinstance(data, list):
            rows = data
        else:
            raise ValueError("Unsupported data type for validation")
            
        for row in rows:
            try:
                schema(**row)
            except Exception as e:
                raise ValueError(f"Validation failed for row {row}: {e}")

    def merge(self, target_table: str, on: Union[str, List[str]], 
              matched_update: Optional[Dict[str, str]] = None, 
              not_matched_insert: Optional[Dict[str, str]] = None,
              data: Union[Any, None] = None,
              batch_size: Optional[int] = None):
        """
        Perform a MERGE INTO operation (Upsert).
        
        Args:
            target_table: The table to merge into.
            on: Column(s) to join on.
            matched_update: Dict of {col: expr} to update when matched.
            not_matched_insert: Dict of {col: expr} to insert when not matched.
            data: Optional PyArrow Table or Pandas DataFrame to merge from.
            batch_size: Optional batch size for data.
        """
        if data is not None:
            # Similar to insert, handle data chunks
            import pyarrow as pa
            import math
            
            if isinstance(data, pd.DataFrame):
                data = pa.Table.from_pandas(data)
            
            rows = data.to_pylist()
            total_rows = len(rows)
            
            if batch_size is None:
                batch_size = total_rows
            
            num_batches = math.ceil(total_rows / batch_size)
            results = []
            
            for i in range(num_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, total_rows)
                batch_rows = rows[start_idx:end_idx]
                
                # Create a VALUES clause for the source
                values_list = []
                for row in batch_rows:
                    row_vals = []
                    for val in row.values():
                        if isinstance(val, str):
                            row_vals.append(f"'{val}'")
                        elif val is None:
                            row_vals.append("NULL")
                        else:
                            row_vals.append(str(val))
                    values_list.append(f"({', '.join(row_vals)})")
                
                values_clause = ", ".join(values_list)
                source_alias = "source"
                # Construct the source subquery
                # We need to cast columns if necessary, but for now assume simple values
                # Dremio VALUES syntax: (val1, val2), ...
                # But we need to alias columns: SELECT * FROM (VALUES ...) AS source(col1, col2)
                cols_def = ", ".join(data.column_names)
                source_sql = f"(VALUES {values_clause}) AS {source_alias}({cols_def})"
                
                results.append(self._compile_and_run_merge(target_table, source_sql, on, matched_update, not_matched_insert))
            
            return results if len(results) > 1 else results[0]
        else:
            # Use current builder as source
            source_sql = f"({self._compile_sql()}) AS source"
            return self._compile_and_run_merge(target_table, source_sql, on, matched_update, not_matched_insert)

        merge_sql = " ".join(parts)
        return self._execute_dml(merge_sql)

    def _compile_and_run_merge(self, target_table, source_sql, on, matched_update, not_matched_insert):
        if isinstance(on, str):
            on = [on]
        
        on_clause = " AND ".join([f"{target_table}.{col} = source.{col}" for col in on])
        
        parts = [f"MERGE INTO {target_table} USING {source_sql} ON ({on_clause})"]
        
        if matched_update:
            updates = ", ".join([f"{col} = {expr}" for col, expr in matched_update.items()])
            parts.append(f"WHEN MATCHED THEN UPDATE SET {updates}")
            
        if not_matched_insert:
            cols = ", ".join(not_matched_insert.keys())
            vals = ", ".join(not_matched_insert.values())
            parts.append(f"WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({vals})")
            
        merge_sql = " ".join(parts)
        return self._execute_dml(merge_sql)

    def scd2(self, target_table: str, on: Union[str, List[str]], 
             track_cols: List[str], 
             valid_from_col: str = "valid_from", 
             valid_to_col: str = "valid_to"):
        """
        Perform SCD2 update.
        1. Closes old records (updates valid_to).
        2. Inserts new records (valid_from = now, valid_to = NULL).
        
        Args:
            target_table: Target table name.
            on: Join key(s).
            track_cols: Columns to check for changes.
            valid_from_col: Name of valid_from column.
            valid_to_col: Name of valid_to column.
        """
        if isinstance(on, str):
            on = [on]
            
        source_sql = f"({self._compile_sql()}) AS source"
        
        # 1. Close Old Records
        # UPDATE target SET valid_to = CURRENT_TIMESTAMP 
        # WHERE EXISTS (SELECT 1 FROM source WHERE target.id = source.id AND (changes))
        # AND target.valid_to IS NULL
        
        join_cond = " AND ".join([f"{target_table}.{k} = source.{k}" for k in on])
        change_cond = " OR ".join([f"{target_table}.{c} <> source.{c}" for c in track_cols])
        
        # Dremio UPDATE with JOIN/FROM syntax
        # UPDATE target SET ... FROM source WHERE ...
        close_sql = f"""
        UPDATE {target_table}
        SET {valid_to_col} = CURRENT_TIMESTAMP
        FROM {source_sql}
        WHERE {join_cond}
          AND {target_table}.{valid_to_col} IS NULL
          AND ({change_cond})
        """
        
        print("Executing SCD2 Close...")
        self._execute_dml(close_sql)
        
        # 2. Insert New/Changed Records
        # INSERT INTO target SELECT ..., CURRENT_TIMESTAMP, NULL FROM source
        # LEFT JOIN target ON ... AND target.valid_to IS NULL
        # WHERE target.id IS NULL OR (changes)
        
        # We need to list all columns to insert.
        # We assume source has all columns except valid_from/valid_to?
        # Or we assume source has same schema as target minus valid_from/valid_to.
        # Let's assume we select * from source.
        
        # We need to construct the SELECT list.
        # source.*, CURRENT_TIMESTAMP, NULL
        
        # We need to handle the WHERE clause for insert
        # It's tricky because we just updated the old records in step 1!
        # So `target.valid_to IS NULL` check might fail if we just closed them?
        # No, we updated them to have a valid_to.
        # So now `target.valid_to IS NULL` will return NOTHING for the changed records.
        # So we can't easily detect "changed" records by joining against current target state 
        # because we just mutated it.
        
        # Solution: We should have identified changes BEFORE updating.
        # Or we use a temporary table for source?
        # Or we rely on the fact that if it's NOT in target (active), it's either new or we just closed it?
        # If we just closed it, it's not active anymore.
        # So if we join source with target (active), and it's missing, it means it's new OR it was just closed.
        # Wait, if we just closed it, it is NO LONGER active.
        # So `LEFT JOIN target ON ... AND target.valid_to IS NULL` will return NULL for target side for both NEW and JUST-CLOSED records.
        # So we can just insert ALL records from source where target is null?
        # YES!
        # If a record didn't change, it is still active in target, so join succeeds, we filter it out.
        # If a record changed, we closed the old one. Now it's not active. Join fails. We insert new one.
        # If a record is new, it's not active. Join fails. We insert new one.
        
        # So the logic holds!
        
        # Construct columns for INSERT
        # We need to know target columns to be safe, but let's assume source columns + valid_from + valid_to match target.
        # We'll select source.*, CURRENT_TIMESTAMP, NULL
        
        insert_sql = f"""
        INSERT INTO {target_table}
        SELECT source.*, CURRENT_TIMESTAMP, NULL
        FROM {source_sql}
        LEFT JOIN {target_table} 
          ON {join_cond} AND {target_table}.{valid_to_col} IS NULL
        WHERE {target_table}.{on[0]} IS NULL
        """
        
        print("Executing SCD2 Insert...")
        return self._execute_dml(insert_sql)

    def delete(self):
        """Delete from table based on filters"""
        if not self.path:
            raise ValueError("Delete requires a table path defined in constructor")
        
        if not self.filters:
            raise ValueError("Delete requires at least one filter to prevent accidental data loss")

        where_clause = " AND ".join(self.filters)
        delete_sql = f"DELETE FROM {self.path} WHERE {where_clause}"
        return self._execute_dml(delete_sql)

    def update(self, updates: dict):
        """Update table based on filters"""
        if not self.path:
            raise ValueError("Update requires a table path defined in constructor")
        
        if not self.filters:
            raise ValueError("Update requires at least one filter")

        set_clause = ", ".join([f"{k} = {v}" for k, v in updates.items()])
        where_clause = " AND ".join(self.filters)
        update_sql = f"UPDATE {self.path} SET {set_clause} WHERE {where_clause}"
        return self._execute_dml(update_sql)

    def _execute_dml(self, sql: str):
        # DML can be executed via Flight or REST. Flight is usually for large result sets.
        # For DML, we might want to use the REST API SQL endpoint if it exists, or just Flight.
        # Flight is fine for DML too, it just returns a result with affected rows.
        return self._execute_flight(sql, "polars")

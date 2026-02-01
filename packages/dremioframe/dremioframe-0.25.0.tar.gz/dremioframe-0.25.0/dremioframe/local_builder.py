import datafusion
import pyarrow as pa
import pandas as pd
from typing import Optional, List, Union

class LocalBuilder:
    def __init__(self, file_path: str, table_name: str = "cache"):
        self.ctx = datafusion.SessionContext()
        self.file_path = file_path
        self.table_name = table_name
        
        # Register the feather file as a table
        # DataFusion supports reading parquet, csv, json, avro.
        # For Feather (Arrow IPC), we might need to read it into memory first or use a specific method if available.
        # DataFusion python bindings usually support register_arrow, register_parquet, etc.
        # Let's try reading into Arrow Table first as Feather support in DF might be limited or require specific setup.
        # Actually, reading into memory is safer for now to ensure compatibility.
        
        try:
            import pyarrow.feather as feather
            self.table = feather.read_table(file_path)
            self.ctx.register_record_batches(table_name, [self.table.to_batches()])
        except Exception as e:
            raise RuntimeError(f"Failed to load cache file {file_path}: {e}")

        self.current_df = self.ctx.table(table_name)

    def select(self, *cols) -> 'LocalBuilder':
        """Select columns."""
        # DataFusion python API: df.select_columns(*cols)
        self.current_df = self.current_df.select_columns(*cols)
        return self

    def filter(self, condition: str) -> 'LocalBuilder':
        """Filter rows using SQL expression."""
        # DataFusion python API: df.filter(col("a") > lit(1))
        # But we want to support SQL string like "a > 1".
        # We can use sql() for this or try to parse.
        # Easiest is to use SQL on the registered table if we haven't modified it too much,
        # but since we are chaining, we are building a DataFrame.
        # DataFusion DataFrame has .filter() which takes an Expression.
        # To support string SQL conditions, we might need to use sql() on the context,
        # but that requires registering the intermediate result.
        
        # Alternative: Use sql() for everything.
        # But we want to maintain the builder pattern.
        
        # Let's use the sql() method on the context for flexibility, 
        # but we need to know the current state.
        # Actually, for simplicity in this "LocalBuilder", let's rely on `sql` method primarily
        # or map simple string conditions if possible.
        
        # DataFusion's `functions` module has `col`, `lit`.
        # Parsing string "a > 1" to Expression is not directly exposed easily without sql parser.
        
        # Strategy: Register the current dataframe as a temporary view and run SQL.
        temp_name = f"temp_{id(self)}"
        self.ctx.register_table(temp_name, self.current_df)
        self.current_df = self.ctx.sql(f"SELECT * FROM {temp_name} WHERE {condition}")
        self.ctx.deregister_table(temp_name)
        return self

    def group_by(self, *cols) -> 'LocalBuilder':
        """Group by columns."""
        # This returns a DataFrame, but we can't chain agg() easily like DremioBuilder
        # unless we wrap it.
        # DremioBuilder.group_by returns self, and stores state.
        # Here we are executing immediately (lazy execution plan).
        
        # We need to support .agg() next.
        # Let's store the grouping state.
        self._group_cols = cols
        return self

    def agg(self, **kwargs) -> 'LocalBuilder':
        """Aggregate."""
        # kwargs: new_col="func(col)"
        # DataFusion agg takes list of expressions.
        from datafusion import functions as f
        from datafusion import col
        
        if not hasattr(self, '_group_cols'):
             raise ValueError("agg() must be called after group_by()")
             
        # We need to parse "func(col)" string to Expressions.
        # Again, SQL is easier.
        
        select_clause = ", ".join([f"{expr} AS {name}" for name, expr in kwargs.items()])
        group_clause = ", ".join(self._group_cols)
        
        temp_name = f"temp_{id(self)}"
        self.ctx.register_table(temp_name, self.current_df)
        
        sql = f"SELECT {group_clause}, {select_clause} FROM {temp_name} GROUP BY {group_clause}"
        self.current_df = self.ctx.sql(sql)
        self.ctx.deregister_table(temp_name)
        
        del self._group_cols
        return self

    def order_by(self, *cols, ascending=True) -> 'LocalBuilder':
        """Order by."""
        # DataFusion sort.
        # SQL: ORDER BY col1 [ASC|DESC], ...
        # Simplified: assume all same direction or use SQL string in cols
        
        order_clause = ", ".join(cols)
        if not ascending:
            # This is a simplification. If user passes ["a", "b"], we make it "a, b DESC" which applies to b?
            # SQL: ORDER BY a, b DESC
            # If user wants mixed, they should pass strings like "a ASC", "b DESC"
            pass
            
        temp_name = f"temp_{id(self)}"
        self.ctx.register_table(temp_name, self.current_df)
        
        direction = "ASC" if ascending else "DESC"
        # If cols are just names, append direction. If they contain space, assume user specified.
        final_cols = []
        for c in cols:
            if " " in c:
                final_cols.append(c)
            else:
                final_cols.append(f"{c} {direction}")
        
        sql = f"SELECT * FROM {temp_name} ORDER BY {', '.join(final_cols)}"
        self.current_df = self.ctx.sql(sql)
        self.ctx.deregister_table(temp_name)
        return self

    def limit(self, n: int) -> 'LocalBuilder':
        self.current_df = self.current_df.limit(n)
        return self

    def sql(self, sql: str) -> 'LocalBuilder':
        """Run raw SQL against the current data (aliased as 'cache')."""
        # We need to register current_df as 'cache'
        self.ctx.register_table("cache", self.current_df)
        self.current_df = self.ctx.sql(sql)
        return self

    def collect(self, format: str = "pandas") -> Union[pd.DataFrame, pa.Table]:
        """Collect results."""
        if format == "pandas":
            return self.current_df.to_pandas()
        elif format == "arrow":
            return self.current_df.to_arrow_table()
        else:
            raise ValueError(f"Unknown format: {format}")
            
    def show(self):
        print(self.collect("pandas"))

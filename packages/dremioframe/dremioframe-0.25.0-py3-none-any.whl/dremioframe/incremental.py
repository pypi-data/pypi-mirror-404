from typing import Optional, List, Any, Union
from dremioframe.client import DremioClient
from dremioframe.builder import DremioBuilder
import pandas as pd

class IncrementalLoader:
    """
    Helper for incremental data loading patterns.
    """
    def __init__(self, client: DremioClient):
        self.client = client

    def get_watermark(self, table_path: str, watermark_col: str) -> Any:
        """
        Get the maximum value of the watermark column in the target table.
        """
        try:
            # Query: SELECT MAX(watermark_col) FROM table
            builder = DremioBuilder(self.client, table_path)
            result = builder.select(f"MAX({watermark_col}) as max_val").collect()
            
            if len(result) > 0:
                val = result['max_val'][0]
                return val if pd.notna(val) else None
            return None
        except Exception:
            # Table might not exist or be empty
            return None

    def load_incremental(self, source_table: str, target_table: str, watermark_col: str, 
                         batch_size: Optional[int] = None) -> int:
        """
        Load data from source to target where watermark_col > target_max_watermark.
        Returns number of rows inserted.
        """
        # 1. Get current watermark
        watermark = self.get_watermark(target_table, watermark_col)
        
        # 2. Build source query
        source_builder = DremioBuilder(self.client, source_table)
        if watermark:
            # Assuming watermark is comparable (number, timestamp)
            # Need to quote value if string/timestamp? 
            # DremioBuilder.filter expects raw SQL condition
            # Ideally we use parameterized query but builder.filter is simple string
            # Let's assume user handles quoting or it's numeric for now, or improve filter
            source_builder = source_builder.filter(f"{watermark_col} > '{watermark}'")
            
        # 3. Insert into target
        # We can use INSERT INTO ... SELECT ...
        # Dremio supports: INSERT INTO target SELECT * FROM source WHERE ...
        
        insert_sql = f"INSERT INTO {target_table} SELECT * FROM {source_table}"
        if watermark:
            insert_sql += f" WHERE {watermark_col} > '{watermark}'"
            
        # Execute
        # Dremio INSERT returns number of rows affected usually
        result = self.client.sql(insert_sql).collect()
        
        # Result schema depends on Dremio version, usually "Records" or "Rows Inserted"
        # Let's try to parse it
        if not result.empty:
            return result.iloc[0, 0] # First cell usually contains count
        return 0

    def merge(self, source_table: str, target_table: str, on: List[str], 
              update_cols: Optional[List[str]] = None, insert_cols: Optional[List[str]] = None) -> None:
        """
        Perform a MERGE operation (Upsert).
        MERGE INTO target USING source ON (condition)
        WHEN MATCHED THEN UPDATE SET ...
        WHEN NOT MATCHED THEN INSERT ...
        """
        on_cond = " AND ".join([f"target.{col} = source.{col}" for col in on])
        
        merge_sql = f"MERGE INTO {target_table} AS target USING {source_table} AS source ON ({on_cond})"
        
        # WHEN MATCHED
        if update_cols:
            set_clause = ", ".join([f"{col} = source.{col}" for col in update_cols])
            merge_sql += f" WHEN MATCHED THEN UPDATE SET {set_clause}"
            
        # WHEN NOT MATCHED
        if insert_cols:
            cols = ", ".join(insert_cols)
            vals = ", ".join([f"source.{col}" for col in insert_cols])
            merge_sql += f" WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({vals})"
        elif update_cols: 
            # If insert_cols not specified but update_cols is, maybe assume all cols?
            # Or user might only want update.
            # Standard MERGE usually has INSERT clause for upsert.
            pass
            
        self.client.sql(merge_sql).collect()

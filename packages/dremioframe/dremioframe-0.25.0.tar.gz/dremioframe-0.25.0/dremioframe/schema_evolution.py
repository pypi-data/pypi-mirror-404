from typing import Dict, List, Any, Optional, Tuple
from dremioframe.client import DremioClient
import pandas as pd

class SchemaManager:
    """
    Manages schema evolution for Dremio tables.
    """
    def __init__(self, client: DremioClient):
        self.client = client

    def get_table_schema(self, path: str) -> Dict[str, str]:
        """
        Get the schema of a table as a dictionary of column_name -> data_type.
        """
        # Use catalog API or SQL to get schema
        # Using SQL describe is often reliable
        try:
            # DESCRIBE table returns columns: Column, Type, ...
            df = self.client.sql(f"DESCRIBE {path}").collect()
            schema = {}
            for _, row in df.iterrows():
                schema[row['Column']] = row['Type']
            return schema
        except Exception as e:
            raise ValueError(f"Could not retrieve schema for {path}: {e}")

    def compare_schemas(self, source_schema: Dict[str, str], target_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Compare two schemas and return differences.
        Returns a dict with:
        - added_columns: {name: type}
        - removed_columns: {name: type}
        - changed_columns: {name: {old_type: ..., new_type: ...}}
        """
        added = {}
        removed = {}
        changed = {}

        source_keys = set(source_schema.keys())
        target_keys = set(target_schema.keys())

        # Added in target (missing in source) -> Wait, usually we compare current (target) vs desired (source) or vice versa.
        # Let's assume we want to migrate FROM source TO target.
        # Or usually: Current DB state vs Desired Code state.
        # Let's define: compare current_schema (db) vs new_schema (code)
        # If new_schema has col A and current doesn't -> Add col A
        
        # Let's stick to: compare(current, new)
        # added: in new but not in current
        # removed: in current but not in new
        
        for col in target_schema:
            if col not in source_schema:
                added[col] = target_schema[col]
            elif source_schema[col] != target_schema[col]:
                changed[col] = {"old_type": source_schema[col], "new_type": target_schema[col]}
        
        for col in source_schema:
            if col not in target_schema:
                removed[col] = source_schema[col]
                
        return {
            "added_columns": added,
            "removed_columns": removed,
            "changed_columns": changed
        }

    def generate_migration_sql(self, table_path: str, diff: Dict[str, Any]) -> List[str]:
        """
        Generate SQL statements to migrate the table to the new schema.
        Note: Dremio Iceberg tables support ALTER TABLE ADD/DROP COLUMN.
        Non-Iceberg tables might require CTAS.
        """
        sqls = []
        
        # Handle Added Columns
        for col, dtype in diff['added_columns'].items():
            sqls.append(f"ALTER TABLE {table_path} ADD COLUMN {col} {dtype}")
            
        # Handle Removed Columns
        for col in diff['removed_columns']:
            sqls.append(f"ALTER TABLE {table_path} DROP COLUMN {col}")
            
        # Handle Changed Columns (Dremio support for type change is limited)
        for col, types in diff['changed_columns'].items():
            # Usually requires explicit CAST or dropping/adding
            # For now, we'll generate a comment or attempt ALTER COLUMN if supported
            sqls.append(f"-- WARNING: Column {col} type change from {types['old_type']} to {types['new_type']} might require manual migration.")
            sqls.append(f"ALTER TABLE {table_path} ALTER COLUMN {col} {types['new_type']}")
            
        return sqls

    def sync_table(self, table_path: str, new_schema: Dict[str, str], dry_run: bool = True) -> List[str]:
        """
        Compare table schema with new_schema and generate/execute migration SQL.
        """
        current_schema = self.get_table_schema(table_path)
        diff = self.compare_schemas(current_schema, new_schema)
        
        sqls = self.generate_migration_sql(table_path, diff)
        
        if not dry_run:
            for sql in sqls:
                if not sql.strip().startswith("--"):
                    self.client.sql(sql).collect()
                    
        return sqls

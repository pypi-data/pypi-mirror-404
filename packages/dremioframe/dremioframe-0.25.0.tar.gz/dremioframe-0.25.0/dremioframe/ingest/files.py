from typing import Optional
import glob
import os
import pandas as pd
import pyarrow as pa

def ingest_files(client, pattern: str, table_name: str, 
                 file_format: Optional[str] = None,
                 write_disposition: str = "replace",
                 recursive: bool = False):
    """
    Ingest multiple files matching a glob pattern into Dremio.
    
    Args:
        client: DremioClient instance.
        pattern: Glob pattern (e.g., "data/*.parquet", "sales_*.csv").
        table_name: Target table name in Dremio.
        file_format: File format ('parquet', 'csv', 'json'). Auto-detected if None.
        write_disposition: 'replace' or 'append'.
        recursive: If True, use ** for recursive glob.
    """
    
    # Find matching files
    files = glob.glob(pattern, recursive=recursive)
    
    if not files:
        raise ValueError(f"No files found matching pattern: {pattern}")
    
    print(f"Found {len(files)} files matching pattern '{pattern}'")
    
    # Detect format from first file if not specified
    if file_format is None:
        ext = os.path.splitext(files[0])[1].lower()
        format_map = {
            '.parquet': 'parquet',
            '.csv': 'csv',
            '.json': 'json',
            '.jsonl': 'json',
            '.ndjson': 'json'
        }
        file_format = format_map.get(ext)
        if file_format is None:
            raise ValueError(f"Cannot auto-detect format for extension: {ext}")
    
    # Read and concatenate all files
    tables = []
    
    for file_path in files:
        print(f"Reading {file_path}...")
        
        if file_format == 'parquet':
            import pyarrow.parquet as pq
            table = pq.read_table(file_path)
        elif file_format == 'csv':
            import pyarrow.csv as csv
            table = csv.read_csv(file_path)
        elif file_format == 'json':
            # PyArrow JSON reader
            import pyarrow.json as json
            table = json.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        tables.append(table)
    
    # Concatenate all tables
    if len(tables) == 1:
        combined_table = tables[0]
    else:
        import pyarrow as pa
        combined_table = pa.concat_tables(tables)
    
    print(f"Total rows: {len(combined_table)}")
    
    # Write to Dremio using builder
    builder = client.table(table_name)
    
    if write_disposition == "replace":
        try:
            client.execute(f"DROP TABLE IF EXISTS {table_name}")
        except Exception:
            pass
        builder.create(table_name, data=combined_table, method="staging")
        
    elif write_disposition == "append":
        try:
            builder.insert(table_name, data=combined_table, method="staging")
        except Exception:
            # Table might not exist, create it
            builder.create(table_name, data=combined_table, method="staging")
    else:
        raise ValueError(f"Unsupported write_disposition: {write_disposition}")
    
    print(f"Successfully ingested {len(files)} files into {table_name}")

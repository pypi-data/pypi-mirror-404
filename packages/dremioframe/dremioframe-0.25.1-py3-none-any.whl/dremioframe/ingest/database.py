from typing import Any, Optional, Union
import pandas as pd

def ingest_database(client, connection_string: str, query: str, table_name: str, 
                    write_disposition: str = "replace", 
                    batch_size: int = 10000,
                    backend: str = "connectorx"):
    """
    Ingest data from a SQL database into Dremio.
    
    Args:
        client: DremioClient instance.
        connection_string: Database connection string (URI).
        query: SQL query to execute on the source database.
        table_name: Target table name in Dremio.
        write_disposition: 'replace' or 'append'.
        batch_size: Number of records to process per batch (only for sqlalchemy backend).
        backend: 'connectorx' (faster, default) or 'sqlalchemy' (more compatible).
    """
    
    df = None
    
    if backend == "connectorx":
        try:
            import connectorx as cx
        except ImportError:
            raise ImportError("connectorx is not installed. Install with `pip install dremioframe[database]`")
            
        print(f"Reading from database using connectorx...")
        # connectorx returns arrow table or pandas df. Let's get pandas for consistency with existing ingest logic
        # or arrow for speed. DremioBuilder accepts both.
        # cx.read_sql returns DataFrame by default
        try:
            df = cx.read_sql(connection_string, query)
        except Exception as e:
            raise RuntimeError(f"connectorx failed: {e}")

    elif backend == "sqlalchemy":
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError("sqlalchemy is not installed. Install with `pip install dremioframe[database]`")
            
        print(f"Reading from database using sqlalchemy...")
        engine = create_engine(connection_string)
        
        # For very large datasets, we might want to chunk.
        # pd.read_sql supports chunksize
        # If batch_size is provided, we can iterate
        
        if batch_size:
            # pd.read_sql with chunksize returns an iterator
            chunks = pd.read_sql(query, engine, chunksize=batch_size)
            
            first_chunk = True
            for chunk in chunks:
                mode = write_disposition if first_chunk else "append"
                _write_to_dremio(client, table_name, chunk, mode)
                first_chunk = False
            return
        else:
            df = pd.read_sql(query, engine)
            
    else:
        raise ValueError(f"Unknown backend: {backend}")

    if df is not None:
        _write_to_dremio(client, table_name, df, write_disposition)

def _write_to_dremio(client, table_name, data, mode):
    """Helper to write DataFrame to Dremio"""
    if data.empty:
        return

    builder = client.table(table_name)
    
    if mode == "replace":
        try:
            client.execute(f"DROP TABLE IF EXISTS {table_name}")
        except Exception:
            pass
        builder.create(table_name, data=data)
        
    elif mode == "append":
        try:
            builder.insert(table_name, data=data)
        except Exception:
             builder.create(table_name, data=data)
             
    else:
        raise ValueError(f"Unsupported write_disposition: {mode}")

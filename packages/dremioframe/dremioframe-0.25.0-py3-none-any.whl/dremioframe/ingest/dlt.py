from typing import Any, Optional, List, Union
import pyarrow as pa
import pandas as pd

def ingest_dlt(client, source: Any, table_name: str, 
               write_disposition: str = "replace", 
               batch_size: int = 10000,
               schema: Any = None):
    """
    Ingest data from a dlt source into Dremio.
    
    Args:
        client: DremioClient instance.
        source: dlt source or resource object.
        table_name: Target table name in Dremio.
        write_disposition: 'replace', 'append', or 'merge'.
        batch_size: Number of records to process per batch.
        schema: Optional schema definition.
    """
    try:
        import dlt
    except ImportError:
        raise ImportError("dlt is not installed. Please install it with `pip install dremioframe[ingest]`")

    # Normalize source to a list of resources if it's a source
    if hasattr(source, "resources"):
        resources = list(source.resources.values())
    else:
        resources = [source]

    for resource in resources:
        # We iterate over the resource to get data
        # dlt resources are iterables of dicts (usually)
        
        # We'll collect batches and write them
        batch = []
        
        # Determine effective table name
        # If multiple resources, we might want to append resource name to table name?
        # Or user specifies table_name and we assume single resource?
        # Let's assume table_name is the prefix or exact name if single resource.
        
        target_table = table_name
        if len(resources) > 1:
            target_table = f"{table_name}_{resource.name}"
            
        print(f"Ingesting resource '{resource.name}' into '{target_table}'...")
        
        for item in resource:
            batch.append(item)
            
            if len(batch) >= batch_size:
                _write_batch(client, target_table, batch, write_disposition)
                batch = []
                write_disposition = "append" # Subsequent batches always append
                
        if batch:
            _write_batch(client, target_table, batch, write_disposition)

def _write_batch(client, table_name, data, mode):
    df = pd.DataFrame(data)
    if df.empty:
        return

    # Use existing client ingestion methods
    # We can use client.table(name).create/insert/merge
    
    builder = client.table(table_name)
    
    if mode == "replace":
        # Check if table exists, drop if so? 
        # Builder.create with data usually handles CTAS.
        # But if we want to replace, we should drop first.
        try:
            client.execute(f"DROP TABLE IF EXISTS {table_name}")
        except Exception:
            pass
        builder.create(table_name, data=df)
        
    elif mode == "append":
        # Try insert, fallback to create if not exists
        try:
            builder.insert(table_name, data=df)
        except Exception:
             builder.create(table_name, data=df)
             
    elif mode == "merge":
        # Merge requires PK. dlt resources often have primary_key hint.
        # But for now let's just support append/replace or explicit merge via other methods.
        # Fallback to append for now or raise error if merge requested without PK logic
        raise NotImplementedError("Merge mode for dlt not yet fully implemented. Use 'replace' or 'append'.")

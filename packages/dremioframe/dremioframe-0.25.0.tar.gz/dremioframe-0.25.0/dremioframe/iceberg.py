from typing import Optional, List, Any, Dict
import pandas as pd
import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table
from pyiceberg.schema import Schema

class DremioIcebergClient:
    def __init__(self, client):
        self.client = client
        self._catalog = None

    @property
    def catalog(self):
        if self._catalog is None:
            # Determine configuration based on client state (Cloud vs Software)
            # Cloud: https://catalog.dremio.cloud/api/iceberg
            # Software: User must provide URI via some mechanism or we guess?
            # The user request said: "a dremio software user would also have to pass in the url since that may change"
            # We need a way to pass this config. 
            # Ideally, DremioClient should have an 'iceberg_catalog_uri' param or we assume a default for Cloud.
            
            # Default to Cloud if not specified
            import os
            uri = os.getenv("DREMIO_ICEBERG_URI", "https://catalog.dremio.cloud/api/iceberg")
            
            # Construct properties
            props = {
                "uri": uri,
                "type": "rest",
                "header.X-Iceberg-Access-Delegation": "vended-credentials",
                "warehouse": self.client.project_id or os.getenv("DREMIO_PROJECT_ID") or "my_project",
            }
            
            if self.client.pat:
                props["token"] = self.client.pat
                # Only add oauth uri if using Cloud default or explicitly set
                if "dremio.cloud" in uri:
                    props["oauth2-server-uri"] = "https://login.dremio.cloud/oauth/token"
                
            self._catalog = load_catalog("dremio", **props)
        return self._catalog

    def list_namespaces(self) -> List[tuple]:
        """List all namespaces."""
        return self.catalog.list_namespaces()

    def list_tables(self, namespace: str) -> List[str]:
        """List all tables in a namespace."""
        return self.catalog.list_tables(namespace)

    def load_table(self, identifier: str) -> Table:
        """Load a table by identifier (e.g., 'namespace.table')."""
        return self.catalog.load_table(identifier)

    def create_table(self, identifier: str, schema: Schema, location: Optional[str] = None) -> Table:
        """Create a new table."""
        return self.catalog.create_table(identifier, schema, location)

    def drop_table(self, identifier: str):
        """Drop a table."""
        self.catalog.drop_table(identifier)

    def append(self, table_identifier: str, df: pd.DataFrame):
        """Append a Pandas DataFrame to an Iceberg table."""
        table = self.load_table(table_identifier)
        table.append(pa.Table.from_pandas(df))

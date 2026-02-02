from typing import Any, Dict, Optional
from airflow.hooks.base import BaseHook
from dremioframe.client import DremioClient

class DremioHook(BaseHook):
    """
    Interact with Dremio.
    
    :param dremio_conn_id: The connection ID to use.
    """
    conn_name_attr = "dremio_conn_id"
    default_conn_name = "dremio_default"
    conn_type = "dremio"
    hook_name = "Dremio"

    def __init__(self, dremio_conn_id: str = default_conn_name, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dremio_conn_id = dremio_conn_id
        self.client: Optional[DremioClient] = None

    def get_conn(self) -> DremioClient:
        """
        Returns a DremioClient.
        """
        if self.client:
            return self.client

        conn = self.get_connection(self.dremio_conn_id)
        
        # Extract config from connection
        # Host: conn.host
        # Login: conn.login (username)
        # Password: conn.password
        # Extra: JSON dict for PAT, Project ID, etc.
        
        extra = conn.extra_dejson
        
        pat = extra.get("pat") or extra.get("token")
        project_id = extra.get("project_id")
        
        # If PAT is in password field (common pattern for token auth)
        if not pat and not conn.login and conn.password:
            pat = conn.password

        self.client = DremioClient(
            hostname=conn.host,
            port=conn.port or 443,
            username=conn.login,
            password=conn.password,
            pat=pat,
            project_id=project_id,
            tls=extra.get("tls", True),
            disable_certificate_verification=extra.get("disable_certificate_verification", False)
        )
        return self.client

    def get_records(self, sql: str) -> Any:
        """
        Executes the SQL and returns a list of records.
        """
        client = self.get_conn()
        df = client.sql(sql).collect("pandas")
        return df.to_dict(orient="records")

    def get_pandas_df(self, sql: str) -> Any:
        """
        Executes the SQL and returns a Pandas DataFrame.
        """
        client = self.get_conn()
        return client.sql(sql).collect("pandas")

    def run(self, sql: str) -> Any:
        """
        Executes the SQL.
        """
        client = self.get_conn()
        # If it's DML/DDL, we might want to use execute() or just collect()
        # DremioBuilder.collect() handles execution.
        return client.sql(sql).collect("pandas")

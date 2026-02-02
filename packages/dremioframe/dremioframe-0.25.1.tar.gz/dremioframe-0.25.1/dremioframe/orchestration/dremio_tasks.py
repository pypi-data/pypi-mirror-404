from .task import Task
from ..client import DremioClient
import time

class DremioQueryTask(Task):
    """
    Task to run a SQL query on Dremio and wait for completion.
    Supports job cancellation on kill.
    """
    def __init__(self, name: str, client: DremioClient, sql: str, **kwargs):
        super().__init__(name, self._run_query, **kwargs)
        self.client = client
        self.sql = sql
        self.job_id = None

    def _run_query(self, context=None):
        print(f"[{self.name}] Executing SQL: {self.sql}")
        try:
            # Use client.execute (Flight) to execute SQL directly without wrapping
            # This handles both SELECT and DML (CTAS, INSERT, etc.)
            result = self.client.execute(self.sql)
            self.status = "SUCCESS"
            return result
        except Exception as e:
            print(f"[{self.name}] Query failed: {e}")
            self.status = "FAILED"
            raise e

    def on_kill(self):
        if self.job_id:
            print(f"Cancelling Dremio Job {self.job_id}...")
            try:
                self.client.api.post(f"job/{self.job_id}/cancel", json={})
                print("Job cancelled.")
            except Exception as e:
                print(f"Failed to cancel job: {e}")

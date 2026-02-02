from .task import Task
from ..client import DremioClient
import time

class Sensor(Task):
    """Base class for sensors."""
    def __init__(self, name: str, poke_interval: int = 60, timeout: int = 3600, **kwargs):
        super().__init__(name, self._run_sensor, **kwargs)
        self.poke_interval = poke_interval
        self.timeout = timeout
        self.start_time = None

    def _run_sensor(self, context=None):
        self.start_time = time.time()
        while True:
            if self.poke(context):
                print(f"[{self.name}] Condition met.")
                self.status = "SUCCESS"
                return True
            
            if time.time() - self.start_time > self.timeout:
                raise TimeoutError(f"Sensor {self.name} timed out after {self.timeout} seconds")
            
            print(f"[{self.name}] Condition not met, sleeping for {self.poke_interval}s...")
            time.sleep(self.poke_interval)

    def poke(self, context):
        """Override this method to check condition. Return True if met."""
        raise NotImplementedError

class SqlSensor(Sensor):
    """
    Polls a SQL query until it returns rows (or a specific condition).
    By default, checks if query returns any rows.
    """
    def __init__(self, name: str, client: DremioClient, sql: str, **kwargs):
        super().__init__(name, **kwargs)
        self.client = client
        self.sql = sql

    def poke(self, context):
        try:
            # Run query
            df = self.client.query(self.sql, format="pandas")
            # If not empty, condition met
            return not df.empty
        except Exception as e:
            print(f"[{self.name}] Query failed: {e}")
            return False

class FileSensor(Sensor):
    """
    Checks for the existence of a file or folder in Dremio source.
    Uses TABLE(LIST_FILES(...)).
    """
    def __init__(self, name: str, client: DremioClient, path: str, **kwargs):
        super().__init__(name, **kwargs)
        self.client = client
        self.path = path

    def poke(self, context):
        try:
            # Use list_files
            builder = self.client.list_files(self.path)
            df = builder.collect("pandas")
            return not df.empty
        except Exception as e:
            # If path doesn't exist, it might raise error or return empty
            print(f"[{self.name}] Check failed: {e}")
            return False

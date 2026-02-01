from .dremio_tasks import DremioQueryTask
from ..client import DremioClient

class OptimizeTask(DremioQueryTask):
    """
    Runs OPTIMIZE TABLE command on an Iceberg table.
    """
    def __init__(self, name: str, client: DremioClient, table: str, rewrite_data_files: bool = True, **kwargs):
        sql = f"OPTIMIZE TABLE {table}"
        if rewrite_data_files:
            sql += " REWRITE DATA USING BIN_PACK" # Default strategy usually
        super().__init__(name, client, sql, **kwargs)

class VacuumTask(DremioQueryTask):
    """
    Runs VACUUM TABLE command on an Iceberg table.
    """
    def __init__(self, name: str, client: DremioClient, table: str, expire_snapshots: bool = True, retain_last: int = None, older_than: str = None, **kwargs):
        sql = f"VACUUM TABLE {table}"
        
        # Dremio syntax for VACUUM might vary, but assuming standard Iceberg SQL support
        # Actually Dremio uses VACUUM TABLE ... EXPIRE SNAPSHOTS ...
        
        if expire_snapshots:
            sql += " EXPIRE SNAPSHOTS"
            if retain_last:
                sql += f" RETAIN LAST {retain_last}"
            if older_than:
                sql += f" OLDER_THAN '{older_than}'"
                
        super().__init__(name, client, sql, **kwargs)

class ExpireSnapshotsTask(DremioQueryTask):
    """
    Explicit task for expiring snapshots (wrapper around VACUUM or specialized command).
    """
    def __init__(self, name: str, client: DremioClient, table: str, retain_last: int = 5, **kwargs):
        # Dremio specific syntax check
        sql = f"VACUUM TABLE {table} EXPIRE SNAPSHOTS RETAIN LAST {retain_last}"
        super().__init__(name, client, sql, **kwargs)

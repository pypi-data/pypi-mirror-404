from .dremio_tasks import DremioQueryTask
from ..client import DremioClient

class RefreshReflectionTask(DremioQueryTask):
    """
    Triggers a refresh of all reflections on a dataset.
    Uses SQL: ALTER DATASET {dataset} REFRESH REFLECTIONS
    """
    def __init__(self, name: str, client: DremioClient, dataset: str, **kwargs):
        sql = f"ALTER DATASET {dataset} REFRESH REFLECTIONS"
        super().__init__(name, client, sql, **kwargs)

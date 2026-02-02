from typing import List, Dict, Any, Optional
from dremioframe.client import DremioClient
from concurrent.futures import ThreadPoolExecutor, as_completed

class BatchManager:
    """
    Helper for performing batch operations on the Dremio catalog.
    Uses multi-threading to parallelize API requests.
    """
    def __init__(self, client: DremioClient, max_workers: int = 10):
        self.client = client
        self.max_workers = max_workers

    def create_folders(self, paths: List[str]) -> Dict[str, Any]:
        """
        Create multiple folders.
        paths: List of full paths (e.g., "space.folder1", "space.folder2")
        Returns a dict of path -> result (or error).
        """
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self.client.catalog.create_folder, path): path 
                for path in paths
            }
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    results[path] = {"error": str(e)}
        return results

    def delete_items(self, ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple items by ID.
        Returns a dict of id -> success (bool) or error.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_id = {
                executor.submit(self.client.catalog.delete, id): id 
                for id in ids
            }
            for future in as_completed(future_to_id):
                id = future_to_id[future]
                try:
                    future.result()
                    results[id] = True
                except Exception as e:
                    results[id] = {"error": str(e)}
        return results

    def promote_folders(self, ids: List[str]) -> Dict[str, Any]:
        """
        Promote multiple folders to datasets (if supported by API logic).
        Actually, promote usually takes a path or id and format options.
        Assuming default PDS promotion.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Assuming client.catalog.promote_folder(id) exists or similar
            # If not, we might need to implement logic here.
            # Catalog.promote_pds(id, ...)
            future_to_id = {
                executor.submit(self.client.catalog.promote_pds, id): id 
                for id in ids
            }
            for future in as_completed(future_to_id):
                id = future_to_id[future]
                try:
                    results[id] = future.result()
                except Exception as e:
                    results[id] = {"error": str(e)}
        return results

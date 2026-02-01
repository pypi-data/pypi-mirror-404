import requests
from typing import List, Dict, Any, Optional, Union

class Catalog:
    def __init__(self, client):
        self.client = client

    def _get_project_id(self):
        return self.client.project_id

    def _build_url(self, endpoint: str):
        if self.client.project_id:
             return f"{self.client.base_url}/projects/{self.client.project_id}/{endpoint}"
        else:
             return f"{self.client.base_url}/{endpoint}"

    def list_catalog(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        url = self._build_url("catalog")
        
        if path:
             # If path is provided, we might need to use by-path endpoint or just list children of a folder
             # The API docs say: GET /v0/projects/{project_id}/catalog/by-path/{path}
             url = self._build_url(f"catalog/by-path/{path}")

        response = self.client.session.get(url)
        response.raise_for_status()
        data = response.json()
        
        # If it's the root catalog, it returns 'data' list.
        # If it's a folder/source, it returns 'children' list.
        if "data" in data:
            return data["data"]
        elif "children" in data:
            return data["children"]
        else:
            return [data] # It might be a single entity if path pointed to a file/table

    def get_entity(self, path: str) -> Dict[str, Any]:
        url = self._build_url(f"catalog/by-path/{path}")
        response = self.client.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_entity_by_id(self, id: str) -> Dict[str, Any]:
        url = self._build_url(f"catalog/{id}")
        response = self.client.session.get(url)
        response.raise_for_status()
        return response.json()

    def create_source(self, name: str, source_type: str, config: Dict[str, Any]):
        url = self._build_url("catalog")
        payload = {
            "entityType": "source",
            "name": name,
            "type": source_type,
            "config": config
        }
        response = self.client.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def create_folder(self, path: List[str]):
        url = self._build_url("catalog")
        payload = {
            "entityType": "folder",
            "path": path
        }
        response = self.client.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def delete_catalog_item(self, id: str):
        url = self._build_url(f"catalog/{id}")
        response = self.client.session.delete(url)
        response.raise_for_status()

    def update_wiki(self, id: str, content: str, version: str = None):
        """
        Updates the wiki content for a catalog entity.
        Args:
            id: Entity ID.
            content: Wiki text content.
            version: Optional version string (required for updates to avoid 409 Conflict).
        """
        url = self._build_url(f"catalog/{id}/collaboration/wiki")
        payload = {"text": content}
        if version:
            payload["version"] = version
            
        response = self.client.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_wiki(self, id: str) -> Dict[str, Any]:
        """
        Retrieves the wiki content for a catalog entity.
        """
        url = self._build_url(f"catalog/{id}/collaboration/wiki")
        response = self.client.session.get(url)
        # 404 means no wiki exists, return empty dict or None? Dremio API might return 404.
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        return response.json()

    def get_tags(self, id: str) -> List[str]:
        """
        Retrieves the tags for a catalog entity.
        """
        url = self._build_url(f"catalog/{id}/collaboration/tag")
        response = self.client.session.get(url)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return data.get("tags", [])

    def get_tag_info(self, id: str) -> Dict[str, Any]:
        """
        Retrieves the tags and version for a catalog entity.
        Returns dict with 'tags' (List[str]) and 'version' (str).
        """
        url = self._build_url(f"catalog/{id}/collaboration/tag")
        response = self.client.session.get(url)
        if response.status_code == 404:
            return {"tags": [], "version": None}
        response.raise_for_status()
        return response.json()

    def set_tags(self, id: str, tags: List[str], version: str = None):
        """
        Sets the tags for a catalog entity (overwrites existing tags).
        Args:
            id: Entity ID.
            tags: List of tags.
            version: Optional version string (required for updates to avoid 409 Conflict).
        """
        url = self._build_url(f"catalog/{id}/collaboration/tag")
        payload = {"tags": tags}
        if version:
            payload["version"] = version
            
        response = self.client.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def create_view(self, path: List[str], sql: Union[str, Any], context: Optional[List[str]] = None):
        """
        Creates a new virtual dataset (View).
        Args:
            path: List of path components (e.g. ["Space", "View"]).
            sql: SQL string or DremioBuilder object.
            context: Optional list of context path components.
        """
        url = self._build_url("catalog")
        
        # Handle Builder object
        if hasattr(sql, "_compile_sql"):
            sql_str = sql._compile_sql()
        else:
            sql_str = str(sql)

        payload = {
            "entityType": "dataset",
            "type": "VIRTUAL_DATASET",
            "path": path,
            "sql": sql_str
        }
        if context:
            payload["sqlContext"] = context
            
        response = self.client.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def update_view(self, id: str, path: List[str], sql: Union[str, Any], context: Optional[List[str]] = None, tag: Optional[str] = None):
        """
        Updates an existing virtual dataset (View).
        If 'tag' (version) is not provided, it will be fetched automatically.
        """
        
        # Handle Builder object
        if hasattr(sql, "_compile_sql"):
            sql_str = sql._compile_sql()
        else:
            sql_str = str(sql)
        
        # If tag is missing, fetch current version
        if not tag:
            current = self.get_entity_by_id(id)
            tag = current.get("tag")

        url = self._build_url(f"catalog/{id}")
        payload = {
            "entityType": "dataset",
            "type": "VIRTUAL_DATASET",
            "id": id,
            "path": path,
            "sql": sql_str,
            "tag": tag
        }
        if context:
            payload["sqlContext"] = context

        response = self.client.session.put(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_lineage(self, id: str) -> Dict[str, Any]:
        """
        Retrieves the lineage graph for a dataset.
        """
        url = self._build_url(f"catalog/{id}/graph")
        response = self.client.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_grants(self, id: str) -> Dict[str, Any]:
        """
        Retrieves the grants for a catalog entity.
        """
        url = self._build_url(f"catalog/{id}/grants")
        response = self.client.session.get(url)
        response.raise_for_status()
        return response.json()

    def set_grants(self, id: str, grants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sets the grants for a catalog entity.
        Args:
            id: Entity ID.
            grants: List of grant objects (e.g. [{"granteeType": "USER", "id": "...", "privileges": ["SELECT"]}]).
        """
        url = self._build_url(f"catalog/{id}/grants")
        payload = {"grants": grants}
        response = self.client.session.put(url, json=payload)
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

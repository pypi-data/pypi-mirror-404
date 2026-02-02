import aiohttp
import asyncio
from typing import Optional, Dict, Any

class AsyncDremioClient:
    def __init__(self, pat: str, hostname: str = "data.dremio.cloud", project_id: Optional[str] = None):
        self.pat = pat
        self.hostname = hostname
        self.project_id = project_id
        self.base_url = f"https://api.dremio.cloud/v0"
        if "dremio.cloud" not in hostname:
             self.base_url = f"http://{hostname}:9047/api/v3"
        
        self.headers = {
            "Authorization": f"Bearer {pat}",
            "Content-Type": "application/json"
        }
        if project_id:
            self.headers["x-dremio-project-id"] = project_id
            
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_catalog_item(self, id: str) -> Dict[str, Any]:
        """Get a catalog item by ID."""
        async with self.session.get(f"{self.base_url}/catalog/{id}") as response:
            response.raise_for_status()
            return await response.json()

    async def get_catalog_by_path(self, path: list[str]) -> Dict[str, Any]:
        """Get a catalog item by path."""
        path_str = ".".join([f'"{p}"' for p in path])
        async with self.session.get(f"{self.base_url}/catalog/by-path/{path_str}") as response:
            response.raise_for_status()
            return await response.json()

    async def execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL via REST API (async)."""
        payload = {"sql": sql}
        async with self.session.post(f"{self.base_url}/sql", json=payload) as response:
            response.raise_for_status()
            return await response.json()

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        async with self.session.get(f"{self.base_url}/job/{job_id}") as response:
            response.raise_for_status()
            return await response.json()

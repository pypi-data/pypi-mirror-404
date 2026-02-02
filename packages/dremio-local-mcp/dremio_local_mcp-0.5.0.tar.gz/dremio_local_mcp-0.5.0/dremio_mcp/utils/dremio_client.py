from typing import Optional, Dict, Any, List
from dremio_cli.client.factory import create_client
from dremio_mcp.config import DremioConfig
# We import BaseClient/CloudClient/SoftwareClient implicitly via usage

class DremioClient:
    def __init__(self, config: DremioConfig):
        # Create client using dremio_cli factory
        self.client = create_client(config.get_dict())
        self.config_data = config.get_dict()
        self.project_id = self.config_data.get("project_id") or self.config_data.get("project")
        # Check URL for cloud heuristic
        url = (self.config_data.get("url") or self.config_data.get("base_url") or "").lower()
        self.is_cloud = "dremio.cloud" in url

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        # Helper to adjust endpoint for Cloud if necessary
        # But _request usually takes path relative to base_url.
        # If client base_url is `https://api.dremio.cloud`, we need to prepend `/v0/projects/{pid}/` if the passed endpoint is `catalog/...`
        # BUT dremio_cli might handle this? 
        # Actually dremio_cli is mostly Software focused or minimal.
        # If we pass specific endpoint `v0/projects/...`, requests usually appends to base.
        # So we should construct the full relative path in the Tool, and pass it here.
        # Just return result.
        
        # Map method to client functions
        if method.upper() == "GET":
            return self.client.get(endpoint, params=kwargs.get("params"))
        elif method.upper() == "POST":
            return self.client.post(endpoint, data=kwargs.get("json") or kwargs.get("data"))
        elif method.upper() == "PUT":
            return self.client.put(endpoint, data=kwargs.get("json") or kwargs.get("data"))
        elif method.upper() == "DELETE":
            return self.client.delete(endpoint)
        else:
            raise ValueError(f"Unsupported method: {method}")

    def post_sql(self, sql: str, context: Optional[List[str]] = None) -> str:
        """Executes SQL and returns Job ID."""
        # dremio_cli.execute_sql returns the FULL job object usually, or the response dict.
        # Based on source: return self.post("sql", data=data)
        # Response for POST /sql is usually the Job object.
        response = self.client.execute_sql(sql, context=context)
        return response["id"]

    def get_job_results(self, job_id: str, offset: int = 0, limit: int = 500) -> Dict[str, Any]:
        return self.client.get_job_results(job_id, offset=offset, limit=limit)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        return self.client.get_job(job_id)

    def wait_for_job(self, job_id: str, timeout: int = 60) -> Dict[str, Any]:
        import time
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_job_status(job_id)
            state = status.get("jobState")
            if state == "COMPLETED":
                return status
            if state in ["FAILED", "CANCELED"]:
                raise RuntimeError(f"Job {job_id} failed: {status.get('errorMessage')}")
            time.sleep(1)
        raise TimeoutError(f"Job {job_id} timed out.")

    def get_catalog_item(self, path: Optional[List[str]] = None, id: Optional[str] = None) -> Dict[str, Any]:
        if id:
             return self.client.get_catalog_item(id)
        if path:
            path_str = ".".join(path) if isinstance(path, list) else path # path should be string for by_path?
            # Wait, dremio_cli expects path string usually "space.folder.table" or "space/folder/table"?
            # get_catalog_item_by_path signature: (path: str)
            # Dremio API by-path endpoint takes path components? No, usually encoded path.
            # safe bet: if path is list, join with quote or just dot?
            # API expects: /catalog/by-path/foo/bar/baz
            # dremio_cli does: f"catalog/by-path/{path}"
            # So if we pass "foo/bar/baz" it works.
            if isinstance(path, list):
                path_str = "/".join(path)
            else:
                path_str = path
            return self.client.get_catalog_item_by_path(path_str)
        raise ValueError("Must provide either path or id")

    def create_view(self, sql: str, path: List[str]) -> Dict[str, Any]:
        # dremio_cli create_view expects view_data dict
        # view_data = {"entityType": "dataset", "type": "VIRTUAL_DATASET", "path": path, "sql": sql}
        view_data = {
            "entityType": "dataset",
            "type": "VIRTUAL_DATASET",
            "path": path,
            "sql": sql
        }
        return self.client.create_view(view_data)

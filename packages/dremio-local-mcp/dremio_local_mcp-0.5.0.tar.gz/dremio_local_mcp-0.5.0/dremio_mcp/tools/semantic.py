from fastmcp import FastMCP
from dremio_mcp.utils.dremio_client import DremioClient
import json

def register(server: FastMCP, client: DremioClient):

    @server.tool()
    def create_view(sql: str, path: str) -> str:
        """
        Create a new virtual dataset (view) at the specified path.
        path should be dot-delimited (e.g., "Space.Folder.NewViewName").
        """
        try:
            # Use SQL for robustness and idempotency
            # split path to quote individual parts
            path_parts = path.split(".")
            quoted_path = ".".join([f'"{p}"' for p in path_parts])
            
            ddl = f'CREATE OR REPLACE VIEW {quoted_path} AS {sql}'
            
            job_id = client.post_sql(ddl)
            client.wait_for_job(job_id)
            
            return f"Successfully created/updated view at {path}"
        except Exception as e:
            return f"Error creating view: {e}"

    @server.tool()
    def update_wiki(entity_id: str, content: str) -> str:
        """
        Update the wiki documentation for a dataset.
        entity_id: The ID of the dataset.
        """
        try:
            payload = {"text": content}
            
            if client.is_cloud and client.project_id:
                endpoint = f"projects/{client.project_id}/catalog/{entity_id}/collaboration/wiki"
            else:
                # Software fallback (usually base_url includes /api/v3)
                endpoint = f"catalog/{entity_id}/collaboration/wiki"
            
            # Get current version for optimistic locking
            try:
                current = client._request("GET", endpoint)
                version = current.get("version")
            except:
                version = None

            payload = {"text": content, "version": version}
            client._request("POST", endpoint, json=payload)
            return f"Successfully updated wiki for {entity_id}"
        except Exception as e:
            error_details = str(e)
            if hasattr(e, "response"):
                 error_details += f" | Status: {getattr(e.response, 'status_code', 'N/A')} | Body: {getattr(e.response, 'text', 'N/A')}"
            return f"Error updating wiki: {error_details}"

    @server.tool()
    def add_tags(entity_id: str, tags: list[str]) -> str:
        """
        Add tags to a dataset.
        tags: List of strings.
        """
        try:
            if client.is_cloud and client.project_id:
                 base_endpoint = f"projects/{client.project_id}/catalog/{entity_id}/collaboration/tag"
            else:
                 base_endpoint = f"catalog/{entity_id}/collaboration/tag"

            # Get existing
            try:
                current = client._request("GET", base_endpoint)
                existing_tags = current.get("tags", [])
                version = current.get("version")
            except:
                existing_tags = []
                version = None
            
            new_tags = list(set(existing_tags + tags))
            payload = {"tags": new_tags, "version": version}
            client._request("POST", base_endpoint, json=payload)
            return f"Successfully updated tags. Current tags: {new_tags}"
        except Exception as e:
             error_details = str(e)
             if hasattr(e, "response"):
                  error_details += f" | Status: {getattr(e.response, 'status_code', 'N/A')} | Body: {getattr(e.response, 'text', 'N/A')}"
             return f"Error adding tags: {error_details}"

    @server.tool()
    def get_semantic_context(path: str) -> str:
        """
        Retrieve semantic info (ID, Path, Type) for a path to help with IDs for other tools.
        """
        try:
            path_list = path.split(".")
            data = client.get_catalog_item(path=path_list)
            return json.dumps({
                "id": data.get("id"),
                "path": data.get("path"),
                "type": data.get("type"),
                "entityType": data.get("entityType")
            }, indent=2)
        except Exception as e:
            return f"Error resolving path: {e}"


    @server.tool()
    def plan_semantic_layer(goal: str) -> str:
        """
        Propose a semantic layer structure (Spaces, Folders, Views) based on a high-level goal.
        Returns executable DDL (SQL) to create the structure.
        
        This tool automatically scans your local `~/dremiodocs` folder for relevant best practices.
        """
        try:
             # Import helper inside function to avoid circular deps if any
             from dremio_mcp.utils.docs_helper import query_docs
             docs_context = query_docs(goal) or query_docs("best practices") or ""
        except:
             docs_context = "(Docs integration unavailable)"

        # Generate a plan prompt
        import textwrap
        
        return textwrap.dedent(f"""
        # Semantic Layer Plan: {goal}
        
        {docs_context}
        
        ## Proposed Architecture (DDL)
        
        Run these commands in Dremio (or via `execute_query`) to build your layer.
        
        ### 1. Spaces & Folders
        ```sql
        -- Create necessary spaces if they don't exist
        -- Note: Dremio SQL currently supports creating spaces via API/UI mostly, 
        -- but we can simulate structure via Folders in a 'Business' space.
        
        -- Assumption: 'Business' space exists.
        ```
        
        ### 2. Silver Layer (Cleaned/Joined)
        ```sql
        -- Example View: Joined Customer Orders
        CREATE OR REPLACE VIEW "Business"."Layer_Silver"."CustomerOrders" AS
        SELECT 
            o.order_id,
            o.order_date,
            c.customer_name,
            c.segment
        FROM "Raw"."Orders" o
        JOIN "Raw"."Customers" c ON o.customer_id = c.customer_id;
        ```
        
        ### 3. Gold Layer (Business Logic/Aggregates)
        ```sql
        -- Example View: Monthly Sales by Segment
        CREATE OR REPLACE VIEW "Business"."Layer_Gold"."MonthlyWebSales" AS
        SELECT
            EXTRACT(MONTH FROM order_date) as month,
            segment,
            COUNT(*) as total_orders
        FROM "Business"."Layer_Silver"."CustomerOrders"
        GROUP BY 1, 2;
        ```
        
        ## Next Steps
        1. **Review**: Check if "Raw" tables exist.
        2. **Execute**: Run the `CREATE OR REPLACE VIEW` commands using `execute_query`.
        3. **Document**: Use `update_wiki` to add business context to the new Gold views.
        """)

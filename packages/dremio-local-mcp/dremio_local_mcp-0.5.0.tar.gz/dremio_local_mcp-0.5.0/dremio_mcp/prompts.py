from fastmcp import FastMCP
from dremio_mcp.utils.dremio_client import DremioClient

def register(server: FastMCP, client: DremioClient):
    
    # --- Analysis & Documentation (1-5) ---

    @server.prompt()
    def analyze_dataset(path: str) -> str:
        """
        Comprehensive status report for a dataset (Schema + Wiki + Tags + Recent Activity).
        """
        return f"""
Please analyze the dataset located at `{path}`.
1. Use `get_dataset_schema` to understand the columns and types.
2. Use `get_context` to retrieve any existing Wiki documentation and tags.
3. Use `list_jobs` (if applicable) or `recommend_performance_improvements` to check for recent query issues.
4. Summary: Provide a comprehensive status report on the health, documentation coverage, and usage of this dataset.
"""

    @server.prompt()
    def draft_wiki(path: str) -> str:
        """
        Draft documentation for a dataset based on its schema and metadata.
        """
        return f"""
I need you to write a Wiki entry for the dataset `{path}`.
1. Call `get_dataset_schema` to get column names and types.
2. Based on the name and columns, infer the business purpose of the dataset.
3. Draft a markdown Wiki content with:
   - **Description**: What this data represents.
   - **Columns**: A table explaining key columns.
   - **Usage**: Potential analytical questions this dataset answers.
4. Finally, ask me if I want to apply this using `update_wiki`.
"""

    @server.prompt()
    def generate_view(goal: str, source_path: str) -> str:
        """
        Create a Semantic Layer view definition (SQL) following Medallion architecture.
        """
        return f"""
I want to create a curated view in the Semantic Layer based on `{source_path}`.
Goal: {goal}

1. Analyze the source schema (`get_dataset_schema`).
2. Propose a SQL query that:
   - Renames technical column names to business-friendly names (e.g., `cust_id` -> `Customer_ID`).
   - Casts types where appropriate.
   - Adds any necessary calculated fields for the goal.
3. The query should follow "Silver/Gold" layer best practices (clean, consistent).
4. Do NOT create it yet, just show me the SQL and the recommended path (e.g. `Business.Raw_Refined.MyView`).
"""

    @server.prompt()
    def onboard_analyst(space_path: str) -> str:
        """
        Help a new analyst understand the key assets in a specific Space.
        """
        return f"""
I am a new analyst looking at the space `{space_path}`.
1. List the contents of this space (`list_datasets`).
2. For the top 5 most interesting-sounding datasets, fetch their context (`get_context`).
3. specificy which datasets appear to be "Gold" (business-ready) versus "Bronze" (raw).
4. Provide a "Getting Started" guide for this space.
"""

    @server.prompt()
    def compare_schemas(path_a: str, path_b: str) -> str:
        """
        Compare two datasets (e.g. Dev vs Prod) and highlight differences.
        """
        return f"""
Please compare the schema of `{path_a}` vs `{path_b}`.
1. Get schema for A.
2. Get schema for B.
3. Output a differences table:
   - Missing columns.
   - Type mismatches.
   - New columns.
"""

    # --- Optimization & Operations (6-10) ---

    @server.prompt()
    def troubleshoot_job(job_id: str) -> str:
        """
        Analyze a specific job failure and suggest fixes.
        """
        return f"""
The job `{job_id}` failed or is performing poorly.
1. Call `analyze_job` to get the profile and error message.
2. Call `recommend_performance_improvements`.
3. Explain the root cause in simple terms.
4. Suggest the specific SQL change or Dremio configuration change (Reflection) needed to fix it.
"""

    @server.prompt()
    def optimize_query(sql_query: str) -> str:
        """
        Review a SQL query for anti-patterns and performance.
        """
        return f"""
Please optimize this Dremio SQL query:
```sql
{sql_query}
```
1. Identify any anti-patterns (e.g. `SELECT *`, scans on raw files, inefficient joins).
2. Recommend specifically which Reflections (Agg or Raw) would accelerate this.
3. Rewrite the query for better performance or readability.
"""

    @server.prompt()
    def suggest_reflections(dataset_path: str) -> str:
        """
        Propose Reflections for a dataset.
        """
        return f"""
I want to accelerate queries on `{dataset_path}`.
1. Call `scan_reflection_opportunities` (simulated analysis).
2. Based on the columns (`get_dataset_schema`), propose:
   - A **Raw Reflection** (display fields, partition fields).
   - An **Aggregation Reflection** (dimensions, measures) if it looks like fact data.
3. Provide the Dremio SQL syntax to create these reflections (`ALTER DATASET ...`).
"""

    @server.prompt()
    def audit_users(dataset_path: str) -> str:
        """
        Who has been using this dataset?
        """
        return f"""
I need an audit of `{dataset_path}`.
1. Check `list_jobs` (filtered by this dataset if possible, or just recent jobs).
2. Extract the unique `User` fields from the jobs interacting with this dataset.
3. Summarize: "Users X, Y, Z have queried this recently."
"""

    @server.prompt()
    def find_unused_assets(space_path: str) -> str:
        """
        Identify potentially unused datasets in a space.
        """
        return f"""
Help me clean up `{space_path}`.
1. List all datasets in the space.
2. For each dataset, check if it appears in the recent job history (`list_jobs`).
3. Flag any datasets that have 0 recent queries as "Candidate for Archive".
"""

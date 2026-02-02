from fastmcp import FastMCP
from dremio_mcp.utils.dremio_client import DremioClient
import re

def register(server: FastMCP, client: DremioClient):
    
    @server.tool()
    def execute_query(sql: str, context: list[str] = None, mode: str = "run", format: str = "text") -> str:
        """
        Execute a SQL query or get its execution plan.
        
        Args:
            sql: The SQL query to run.
            context: List of context paths (e.g., ["Space", "Folder"]).
            mode: "run" (default), "dry_run" (checks validty), or "explain" (returns cost/plan).
            format: "text" (default) or "json".
            
        Safety: 
        - Destructive keywords (DROP, DELETE, TRUNCATE, ALTER) are BLOCKED unless mode="run" AND confirmed with magic comment /* --CONFIRM-DESTRUCTION-- */.
        - "dry_run" uses EXPLAIN PLAN to validate without execution.
        """
        import json
        
        sql_upper = sql.upper().strip()
        destructive_keywords = ["DROP ", "DELETE ", "TRUNCATE ", "ALTER "]
        
        is_destructive = any(kw in sql_upper for kw in destructive_keywords)
        is_confirmed = "--CONFIRM-DESTRUCTION--" in sql
        
        # Guardrails
        if is_destructive and mode == "run" and not is_confirmed:
            return (
                f"SAFETY BLOCK: The query contains destructive keywords ({destructive_keywords}).\n"
                "If you are sure, you must:\n"
                "1. Add the comment /* --CONFIRM-DESTRUCTION-- */ to your SQL.\n"
                "2. OR run with mode='dry_run' to test validity first."
            )

        try:
            # Handle Dry Run / Explain
            if mode in ["dry_run", "explain"]:
                explain_sql = f"EXPLAIN PLAN FOR {sql}"
                # We reuse post_sql assuming it handles general SQL
                # But typically EXPLAIN PLAN returns text results
                job_id = client.post_sql(explain_sql, context=context)
                client.wait_for_job(job_id)
                results = client.get_job_results(job_id)
                rows = results.get("rows", [])
                
                if format == "json":
                    return json.dumps(rows, indent=2)
                else:
                    # Format explain plan (usually in 'text' col or similar)
                    output = [f"Explain Plan ({mode}):"]
                    for row in rows:
                        # Dremio explain output structure varies, usually multiple rows of text
                        output.append(str(row))
                    return "\n".join(output)

            # Normal Execution
            job_id = client.post_sql(sql, context=context)
            
            # Wait for completion
            client.wait_for_job(job_id)
            
            # Fetch results
            results = client.get_job_results(job_id)
            rows = results.get("rows", [])
            
            if not rows:
                return "Query completed successfully (No rows returned)."
            
            # Formatter
            if format == "json":
                return json.dumps(rows, indent=2, default=str)
            else:
                # Text Table Formatter
                if len(rows) > 50:
                    display_rows = rows[:50]
                    truncated = True
                else:
                    display_rows = rows
                    truncated = False
                
                output = []
                if display_rows:
                    headers = list(display_rows[0].keys())
                    
                    # Markdown Table
                    header_line = "| " + " | ".join(headers) + " |"
                    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
                    output.append(header_line)
                    output.append(sep_line)
                    
                    for row in display_rows:
                        values = [str(row.get(h, "")).replace("\n", " ") for h in headers]
                        output.append("| " + " | ".join(values) + " |")
                
                res_str = "\n".join(output)
                if truncated:
                    res_str += f"\n\n... (Showing 50 of {len(rows)} rows. Use format='json' or limit your query for more.)"
                return res_str

        except Exception as e:
            return f"Error executing query: {e}"

from fastmcp import FastMCP
from dremio_mcp.utils.dremio_client import DremioClient

def register(server: FastMCP, client: DremioClient):
    
    @server.tool()
    def scan_reflection_opportunities() -> str:
        """
        Scan for datasets that might benefit from reflections by analyzing recent slow jobs.
        """
        try:
            # 1. Query sys.jobs for slow queries (> 2s)
            jobs_found = False
            rows = []
            
            # Strategy: Try Software table path, then Cloud table path
            attempts = [
                {
                    "table": "sys.jobs",
                    "sql": "SELECT query AS query_text, queried_datasets AS dataset_graph FROM sys.jobs WHERE execution_cpu_time_millis > 2000 AND submitted_ts > DATE_SUB(CURRENT_DATE, 7) AND status = 'COMPLETED' LIMIT 20"
                },
                {
                    "table": "sys.project.history.jobs",
                    # Cloud: use execution_cpu_time_ns > 2s (2e9 ns)
                    "sql": "SELECT query AS query_text, dataset_graph FROM sys.project.history.jobs WHERE execution_cpu_time_ns > 2000000000 AND status = 'COMPLETED' LIMIT 20"
                }
            ]
            
            last_error = None
            errors = []
            for attempt in attempts:
                try:
                    job_id = client.post_sql(attempt["sql"])
                    client.wait_for_job(job_id)
                    results = client.get_job_results(job_id)
                    rows = results.get("rows", [])
                    _ = rows # Access to ensure valid
                    jobs_found = True
                    break
                except Exception as e:
                    errors.append(f"Table {attempt.get('table')}: {str(e)}")
                    last_error = e
                    continue
            
            if not jobs_found:
                if errors:
                     return f"Error scanning reflections. Details: {'; '.join(errors)}"
                return "No slow jobs found."

            if not rows:
                return "No slow jobs (> 2s) found in the last 7 days to analyze."

            # 2. Analyze results
            recommendations = []
            import json
            
            # Simple heuristic: Count dataset usage in slow queries
            dataset_counts = {}
            
            for row in rows:
                # dataset_graph is a JSON string list of lists of datasets usually
                # or we can parse query_text. dataset_graph is more reliable if available.
                # In Dremio sys.jobs, dataset_graph is often null for older versions, but let's try.
                graph = row.get("dataset_graph")
                if graph:
                    try:
                        datasets = json.loads(graph)
                        for ds_obj in datasets:
                            # dataset path is usually in 'datasetPath' or derived
                            # Dremio sys.jobs structure varies.
                            # Fallback to query text regex if needed.
                            pass
                    except:
                        pass
                
                # Regex fallback for FROM clause
                query = row.get("query_text", "")
                # Find "FROM space.folder.table"
                import re
                matches = re.findall(r'FROM\s+([a-zA-Z0-9_.\"]+)', query, re.IGNORECASE)
                for match in matches:
                    clean_match = match.replace('"', '')
                    dataset_counts[clean_match] = dataset_counts.get(clean_match, 0) + 1

            # 3. Generate Recommendations
            if not dataset_counts:
                return "Analyzed slow jobs but could not reliably identify datasets. (Try creating Raw Reflections on your largest tables)."

            report = ["# Reflection Recommendations", "", "Based on analyzing slow queries from the last 7 days:", ""]
            
            sorted_ds = sorted(dataset_counts.items(), key=lambda x: x[1], reverse=True)
            
            for ds, count in sorted_ds[:5]:
                report.append(f"## Dataset: {ds}")
                report.append(f"- **Usage in Slow Queries**: {count} times")
                report.append(f"- **Recommendation**: Create a RAW Refection to accelerate scans.")
                report.append(f"- **Command**:")
                report.append(f"  ```sql")
                report.append(f"  ALTER DATASET {ds} CREATE RAW REFLECTION {ds.split('.')[-1]}_raw USING DISPLAY;")
                report.append(f"  ```")
                report.append("")
                
            return "\n".join(report)

        except Exception as e:
            return f"Error scanning for reflections: {e}"

from fastmcp import FastMCP
from dremio_mcp.utils.dremio_client import DremioClient

def register(server: FastMCP, client: DremioClient):
    
    @server.tool()
    def list_jobs(filter_str: str = "") -> str:
        """
        List recent jobs using System Tables (SQL).
        filter_str: SQL WHERE clause fragment (e.g. "user_name = 'gnarly'").
        """
    @server.tool()
    def list_jobs(filter_str: str = "") -> str:
        """
        List recent jobs using System Tables (SQL).
        filter_str: SQL WHERE clause fragment (e.g. "user_name = 'gnarly'").
        """
        try:
            where_clause = f"WHERE {filter_str}" if filter_str else ""
            
            attempts = [
                {   # Software
                    "sql": f"SELECT job_id, status, user_name, query AS query_text FROM sys.jobs {where_clause} ORDER BY submitted_ts DESC LIMIT 10"
                },
                {   # Cloud
                    "sql": f"SELECT job_id, status, user_name, query AS query_text FROM sys.project.history.jobs {where_clause} ORDER BY execution_start_epoch DESC LIMIT 10"
                }
            ]
            
            rows = []
            errors = []
            for attempt in attempts:
                try:
                    job_id = client.post_sql(attempt["sql"])
                    client.wait_for_job(job_id)
                    res = client.get_job_results(job_id)
                    rows = res.get("rows", [])
                    break
                except Exception as e:
                    errors.append(f"{attempt.get('sql').split('FROM')[1].split()[0]}: {str(e)}")
                    continue
            
            if not rows:
                if errors:
                    return f"Error listing jobs: {'; '.join(errors)}"
                return "No jobs found."
                
            output = ["Recent Jobs:"]
            for job in rows:
                jid = job.get("job_id")
                state = job.get("status")
                user = job.get("user_name")
                query_snippet = str(job.get("query_text", ""))[:50].replace("\n", " ")
                output.append(f"- {jid} [{state}] ({user}): {query_snippet}...")
            return "\n".join(output)
        except Exception as e:
            return f"Error listing jobs: {e}"

    @server.tool()
    def analyze_job(job_id: str) -> str:
        """
        Retrieve details for a specific job via System Tables.
        """
        try:
            attempts = [
                {   # Software
                    "sql": f"SELECT * FROM sys.jobs WHERE job_id = '{job_id}'"
                },
                {   # Cloud
                    "sql": f"SELECT *, query AS query_text, rows_scanned AS scanned_rows, execution_cpu_time_ns/1000000 AS dur_calc FROM sys.project.history.jobs WHERE job_id = '{job_id}'"
                }
            ]
            
            job = None
            errors = []
            for attempt in attempts:
                try:
                    jid = client.post_sql(attempt["sql"])
                    client.wait_for_job(jid)
                    res = client.get_job_results(jid)
                    rows = res.get("rows", [])
                    if rows:
                        job = rows[0]
                        break
                except Exception as e:
                    # Log error logic
                    errors.append(f"Attempt failed: {e}")
                    continue
            
            if not job:
                return f"Job {job_id} not found. Details: {'; '.join(errors)}"
            
            return f"""
Job ID: {job.get('job_id')}
State: {job.get('status')}
User: {job.get('user_name')}
Rows Scanned: {job.get('scanned_rows', job.get('rows_scanned', 'N/A'))}
Duration: {job.get('dur_calc', job.get('execution_cpu_time_millis', 'N/A'))}ms
Query:
{job.get('query_text', job.get('query','N/A'))}
"""
        except Exception as e:
            return f"Error analyzing job: {e}"

    @server.tool()
    def recommend_performance_improvements(job_id: str) -> str:
        """
        Analyze a job and suggest improvements (SQL-based stats).
        """
        try:
            attempts = [
                {   # Software (assume bytes_scanned exists or input_bytes)
                    "sql": f"SELECT *, query AS query_text FROM sys.jobs WHERE job_id = '{job_id}'"
                },
                {   # Cloud
                    "sql": f"SELECT *, rows_scanned AS scanned_rows, bytes_scanned AS input_bytes FROM sys.project.history.jobs WHERE job_id = '{job_id}'"
                }
            ]
            
            job = None
            for attempt in attempts:
                try:
                    jid = client.post_sql(attempt["sql"])
                    client.wait_for_job(jid)
                    rows = client.get_job_results(jid).get("rows", [])
                    if rows:
                        job = rows[0]
                        break
                except:
                    continue
            
            if not job:
                return "Job not found."

            recommendations = []
            
            if job.get("status") == "FAILED":
                 return f"Job Failed. Error: {job.get('error_msg', 'Unknown')}. Fix error first."
            
            # Helper to get input bytes from various possible keys
            ib = job.get("input_bytes") or job.get("bytes_scanned") or 0
            scanned = int(ib)
            if scanned > 1_000_000_000:
                recommendations.append("- Large scan (>1GB). Consider Reflections.")
                
            # Accelerated
            if "accelerated" in job:
                if not job["accelerated"]:
                    recommendations.append("- query was NOT accelerated.")
            
            if not recommendations:
                recommendations.append("No obvious issues found from system table stats.")
                
            return "Performance Recommendations:\n" + "\n".join(recommendations)

        except Exception as e:
            return f"Error recommending improvements: {e}"

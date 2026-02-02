import sys
import os
sys.path.append(os.getcwd())

from dremio_mcp.config import DremioConfig
from dremio_mcp.utils.dremio_client import DremioClient
import json

TEST_PROFILE = "software"

def diagnose():
    config = DremioConfig(TEST_PROFILE)
    client = DremioClient(config)
    
    print("Querying sys.jobs for one row to inspect columns...")
    try:
        # Select * to see all columns
        job_id = client.post_sql("SELECT * FROM sys.jobs LIMIT 1")
        client.wait_for_job(job_id)
        res = client.get_job_results(job_id)
        rows = res.get("rows", [])
        if rows:
            print("Columns found in sys.jobs:")
            print(json.dumps(list(rows[0].keys()), indent=2))
        else:
            print("No rows in sys.jobs? Empty?")
    except Exception as e:
        print(f"Error querying sys.jobs: {e}")

if __name__ == "__main__":
    diagnose()

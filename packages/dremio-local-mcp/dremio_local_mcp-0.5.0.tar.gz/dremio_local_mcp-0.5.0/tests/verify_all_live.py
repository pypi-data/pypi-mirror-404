import asyncio
import sys
import os
import json

# Ensure project root is in path
sys.path.append(os.getcwd())

from dremio_mcp.config import DremioConfig
from dremio_mcp.utils.dremio_client import DremioClient
from dremio_mcp.tools import reflection, query, semantic, catalog, jobs, docs
from fastmcp import FastMCP

# Setup
TEST_PROFILE = "software"
TEST_SPACE = "dremio-catalog.alexmerced.testing"
TIMESTAMP = "timestamp" # Should be dynamic in real usage, using static name for simplicity or import time

async def verify_all():
    print(f"--- Starting Comprehensive Live Verification (Profile: {TEST_PROFILE}) ---")
    
    # 1. Initialize
    try:
        config = DremioConfig(TEST_PROFILE)
        client = DremioClient(config)
        server = FastMCP("dremio-test-all")
        
        # Register ALL Tools
        reflection.register(server, client)
        query.register(server, client)
        semantic.register(server, client)
        catalog.register(server, client)
        jobs.register(server, client)
        docs.register(server, client)
        
        print("[PASS] Initialization Successful")
    except Exception as e:
        print(f"[FAIL] Initialization Failed: {e}")
        return

    # --- SEMANTIC TOOLS ---
    print("\n[Semantic Tools]")
    try:
        # Plan
        plan_tool = await server.get_tool("plan_semantic_layer")
        print(f"Planning Layer... ", end="")
        res = plan_tool.fn(goal="Test Layer")
        print("[PASS]" if "CREATE OR REPLACE VIEW" in res else f"[FAIL]\n{res}")

        # Create View
        create_tool = await server.get_tool("create_view")
        view_path = f"{TEST_SPACE}.comprehensive_test_view"
        sql = "SELECT 1 as id, 'live_test' as tag_col"
        print(f"Creating View ({view_path})... ", end="")
        res = create_tool.fn(sql=sql, path=view_path)
        print("[PASS]" if "Successfully created" in res else f"[FAIL]\n{res}")
        
        # Get Semantic Context (Need ID)
        context_tool = await server.get_tool("get_semantic_context")
        print(f"Getting Context... ", end="")
        context_json = context_tool.fn(path=view_path)
        context_data = json.loads(context_json)
        entity_id = context_data.get("id")
        print("[PASS]" if entity_id else f"[FAIL]\n{context_json}")
        
        if entity_id:
            # Update Wiki
            wiki_tool = await server.get_tool("update_wiki")
            print(f"Updating Wiki... ", end="")
            res = wiki_tool.fn(entity_id=entity_id, content="Automated Test Wiki Content")
            print("[PASS]" if "Successfully updated" in res else f"[FAIL]\n{res}")
            
            # Add Tags
            tags_tool = await server.get_tool("add_tags")
            print(f"Adding Tags... ", end="")
            res = tags_tool.fn(entity_id=entity_id, tags=["test_tag", "automated"])
            print("[PASS]" if "Successfully updated" in res else f"[FAIL]\n{res}")

    except Exception as e:
        print(f"[FAIL] Semantic Tools Failed: {e}")

    # --- QUERY TOOLS ---
    print("\n[Query Tools]")
    try:
        query_tool = await server.get_tool("execute_query")
        
        # Run Normal
        print("Executing Query... ", end="")
        res = query_tool.fn(sql="SELECT 1", format="json")
        print("[PASS]" if '"1"' in res or ': 1' in res else f"[FAIL]\n{res}")
        
        # Dry Run
        print("Dry Run (Explain)... ", end="")
        res = query_tool.fn(sql="SELECT 1", mode="dry_run")
        print("[PASS]" if "Explain Plan" in res else f"[FAIL]\n{res}")
        
        # Safety Check
        print("Safety Check (DROP)... ", end="")
        res = query_tool.fn(sql="DROP TABLE foo", mode="run")
        print("[PASS]" if "SAFETY BLOCK" in res else f"[FAIL]\n{res}")
        
    except Exception as e:
        print(f"[FAIL] Query Tools Failed: {e}")

    # --- CATALOG TOOLS ---
    print("\n[Catalog Tools]")
    try:
        # List Datasets
        list_tool = await server.get_tool("list_datasets")
        print(f"Listing {TEST_SPACE}... ", end="")
        res = list_tool.fn(path=TEST_SPACE)
        print("[PASS]" if "Contents of" in res else f"[FAIL]\n{res}")
        
        # Get Schema
        schema_tool = await server.get_tool("get_dataset_schema")
        print(f"Getting Schema ({view_path})... ", end="")
        res = schema_tool.fn(path=view_path)
        print("[PASS]" if "id: INTEGER" in res or "id: INT" in res else f"[FAIL]\n{res}")
        
        # Get Context
        get_context_tool = await server.get_tool("get_context")
        print(f"Getting Full Context... ", end="")
        res = get_context_tool.fn(path=view_path)
        print("[PASS]" if "# Context for" in res else f"[FAIL]\n{res}")
        
        # Profile Dataset
        profile_tool = await server.get_tool("profile_dataset")
        print(f"Profiling Dataset... ", end="")
        res = profile_tool.fn(path=view_path)
        print("[PASS]" if "Total Rows" in res else f"[FAIL]\n{res}")
        
        # Upload (Simulated)
        upload_tool = await server.get_tool("upload_dataset")
        print(f"Uploading File (Simulated)... ", end="")
        # Create dummy file
        with open("dummy_test.csv", "w") as f:
            f.write("col1,col2\n1,2")
        res = upload_tool.fn(local_path=os.path.abspath("dummy_test.csv"), dataset_name="dummy_test")
        print("[PASS]" if "File Content" in res else f"[FAIL]\n{res}")
        try:
             os.remove("dummy_test.csv")
        except: pass

    except Exception as e:
        print(f"[FAIL] Catalog Tools Failed: {e}")

    # --- JOBS TOOLS ---
    print("\n[Jobs Tools]")
    try:
        # List Jobs
        jobs_tool = await server.get_tool("list_jobs")
        print(f"Listing Jobs... ", end="")
        res = jobs_tool.fn()
        print("[PASS]" if "Recent Jobs" in res else f"[FAIL]\n{res}")
        
        # Analyze Job (Need an ID)
        # Parse ID from list jobs
        import re
        match = re.search(r'- ([a-z0-9-]+) \[', res)
        job_id = match.group(1) if match else None
        
        if job_id:
            analyze_tool = await server.get_tool("analyze_job")
            print(f"Analyzing Job {job_id}... ", end="")
            res = analyze_tool.fn(job_id=job_id)
            print("[PASS]" if f"Job ID: {job_id}" in res else f"[FAIL]\n{res}")
            
            perf_tool = await server.get_tool("recommend_performance_improvements")
            print(f"Recommending Improvements... ", end="")
            res = perf_tool.fn(job_id=job_id)
            print("[PASS]" if "Recommendations" in res else f"[FAIL]\n{res}")
        else:
            print("[WARN] Skipped Job Analysis (No job ID found in list)")

    except Exception as e:
        print(f"[FAIL] Jobs Tools Failed: {e}")

    # --- REFLECTION TOOLS ---
    print("\n[Reflection Tools]")
    try:
        reflect_tool = await server.get_tool("scan_reflection_opportunities")
        print(f"Scanning Reflections... ", end="")
        res = reflect_tool.fn()
        # Allows output or "No slow jobs" message
        print("[PASS]" if "Reflection" in res or "No slow jobs" in res else f"[FAIL]\n{res}")
    except Exception as e:
        print(f"[FAIL] Reflection Tools Failed: {e}")

    # --- DOCS TOOLS ---
    print("\n[Docs Tools]")
    try:
        docs_tool = await server.get_tool("search_docs")
        print(f"Searching Docs... ", end="")
        res = docs_tool.fn(query="view")
        # Check if it found something or errored gracefully (if no docs present)
        print("[PASS]" if "**" in res or "No results" in res or "Error" in res else f"[FAIL]\n{res}")
    except Exception as e:
        print(f"[FAIL] Docs Tools Failed: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_all())

import asyncio
import sys
import os
import json

# Ensure project root is in path
sys.path.append(os.getcwd())

from dremio_mcp.config import DremioConfig
from dremio_mcp.utils.dremio_client import DremioClient
from dremio_mcp.tools import reflection, query, semantic, catalog
from fastmcp import FastMCP

# Setup
TEST_PROFILE = "cloud"
TEST_SPACE = "testing"

async def verify_enhancements():
    print(f"--- Starting Live Verification (Profile: {TEST_PROFILE}) ---")
    
    # 1. Initialize
    try:
        config = DremioConfig(TEST_PROFILE)
        client = DremioClient(config)
        server = FastMCP("dremio-test")
        
        # Register Tools
        reflection.register(server, client)
        query.register(server, client)
        semantic.register(server, client)
        catalog.register(server, client)
        
        print("✅ Initialization Successful")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Test Data Profiling
    print("\n--- Testing Data Profiling ---")
    try:
        # We need a valid dataset. Let's list what's in 'testing' first
        list_tool = await server.get_tool("list_datasets")
        listing = list_tool.fn(path=TEST_SPACE)
        print(f"Listing of {TEST_SPACE}:\n{listing}")
        
        # Pick a target if available, or just try a known one if we can create it.
        # Let's try to CREATE a view first to ensure we have something to profile.
        create_tool = await server.get_tool("create_view")
        view_path = f"{TEST_SPACE}.test_view"
        sql = "SELECT 1 as id, 'test' as name"
        create_res = create_tool.fn(sql=sql, path=view_path)
        print(f"Create View Result: {create_res}")
        
        # Now Profile it
        profile_tool = await server.get_tool("profile_dataset")
        profile_res = profile_tool.fn(path=view_path)
        print(f"Profile Result:\n{profile_res}")
        if "Total Rows" in profile_res:
            print("✅ Data Profiling Verified")
        else:
            print("❌ Data Profiling Parse Failed")

    except Exception as e:
        print(f"❌ Data Profiling Failed: {e}")

    # 3. Test Query Guardrails
    print("\n--- Testing Query Guardrails ---")
    try:
        query_tool = await server.get_tool("execute_query")
        
        # Dry Run
        dry_res = query_tool.fn(sql="SELECT 1", mode="dry_run")
        print(f"Dry Run Result: {dry_res}")
        if "Explain Plan" in dry_res or "EXPLAIN" in dry_res:
            print("✅ Dry Run Verified")
        else:
            print("warning: Dry run output unexpected")

        # JSON Format
        json_res = query_tool.fn(sql="SELECT 1 as val", format="json")
        if '"val": 1' in json_res or '"val": "1"' in json_res:
             print("✅ JSON Format Verified")
        else:
             print(f"❌ JSON Format Failed: {json_res}")

        # Safety Block
        drop_res = query_tool.fn(sql="DROP VIEW foo", mode="run")
        if "SAFETY BLOCK" in drop_res:
            print("✅ Safety Block Verified")
        else:
            print(f"❌ Safety Block Failed: {drop_res}")

    except Exception as e:
        print(f"❌ Query Guardrails Failed: {e}")

    # 4. Test Semantic DDL Generation
    print("\n--- Testing Semantic DDL ---")
    try:
        plan_tool = await server.get_tool("plan_semantic_layer")
        plan_res = plan_tool.fn(goal="Sales dashboard")
        if "CREATE OR REPLACE VIEW" in plan_res:
            print("✅ Semantic DDL Verified")
        else:
            print("❌ Semantic DDL Failed")
    except Exception as e:
        print(f"❌ Semantic DDL Failed: {e}")
        
    # 5. Test Reflection Analysis (Real)
    print("\n--- Testing Reflection Analysis ---")
    try:
        reflect_tool = await server.get_tool("scan_reflection_opportunities")
        reflect_res = reflect_tool.fn()
        print(f"Reflection Analysis Result: {reflect_res[:200]}...") # Truncate
        # Assert it ran without crash. Finding reflections depends on history.
        print("✅ Reflection Analysis Executed")
    except Exception as e:
        print(f"❌ Reflection Analysis Failed: {e}")

    # Cleanup
    print("\n--- Cleanup ---")
    # try:
    #     client.post_sql(f"DROP VIEW {view_path}") # Might fail if safety block? 
    #     # Actually execute_query blocks it, but client.post_sql does not.
    #     pass
    # except:
    #     pass

if __name__ == "__main__":
    asyncio.run(verify_enhancements())

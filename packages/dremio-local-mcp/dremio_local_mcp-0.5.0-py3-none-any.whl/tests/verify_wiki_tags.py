import asyncio
import sys
import os
import json
import time

sys.path.append(os.getcwd())

from dremio_mcp.config import DremioConfig
from dremio_mcp.utils.dremio_client import DremioClient
from dremio_mcp.tools import semantic, catalog
from fastmcp import FastMCP

TEST_PROFILE = "software"
TEST_SPACE = "dremio-catalog.alexmerced.testing"
VIEW_NAME = "wiki_tags_verification_view"
VIEW_PATH = f"{TEST_SPACE}.{VIEW_NAME}"

async def verify_wiki_tags():
    print(f"--- Starting Wiki/Tags Verification (Profile: {TEST_PROFILE}) ---")
    
    config = DremioConfig(TEST_PROFILE)
    client = DremioClient(config)
    
    print(f"Client Configuration Debug:")
    print(f"- Is Cloud: {client.is_cloud}")
    print(f"- Project ID: {client.project_id}")
    print(f"- Base URL: {client.config_data.get('base_url')}")
    print(f"- Config Keys: {list(client.config_data.keys())}")
    
    server = FastMCP("wiki-test")
    
    semantic.register(server, client)
    catalog.register(server, client)
    
    # 1. Create View
    print(f"\n1. Creating View '{VIEW_PATH}'...")
    try:
        # Use semantic tool (which now uses SQL)
        create_tool = await server.get_tool("create_view")
        sql = "SELECT 1 as id, 'verification' as purpose"
        res = create_tool.fn(sql=sql, path=VIEW_PATH)
        print(f"Result: {res}")
        if "Error" in res:
            print("[FAIL] Could not create view.")
            return
    except Exception as e:
        print(f"[FAIL] Exception creating view: {e}")
        return

    # 2. Get ID (Wait a moment for propagation if needed)
    print("\n2. Retrieving Catalog ID...")
    time.sleep(2) 
    entity_id = None
    try:
        # usage of client directly to ensure we get raw ID
        # split path correctly
        path_list = VIEW_PATH.split(".")
        # Dremio Cloud sometimes prefers path list or string?
        # wrapper:
        item = client.get_catalog_item(path=path_list)
        entity_id = item.get("id")
        print(f"Retrieved ID: {entity_id}")
        print(f"Catalog Item Dump: {json.dumps(item, indent=2)}")
        
        if not entity_id:
            print("[FAIL] ID is null/empty.")
            print(f"Dump: {json.dumps(item, indent=2)}")
            return
    except Exception as e:
        print(f"[FAIL] Exception getting ID: {e}")
        return

    # 3. Update Wiki
    print(f"\n3. Updating Wiki for ID {entity_id}...")
    try:
        wiki_tool = await server.get_tool("update_wiki")
        res = wiki_tool.fn(entity_id=entity_id, content="This is a verified wiki content.")
        print(f"Result: {res}")
    except Exception as e:
        print(f"[FAIL] Wiki Update Failed: {e}")

    # 4. Add Tags
    print(f"\n4. Adding Tags for ID {entity_id}...")
    try:
        tags_tool = await server.get_tool("add_tags")
        res = tags_tool.fn(entity_id=entity_id, tags=["verified", "automated"])
        print(f"Result: {res}")
    except Exception as e:
        print(f"[FAIL] Tags Add Failed: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_wiki_tags())

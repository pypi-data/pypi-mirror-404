import pytest
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from dremio_mcp.config import DremioConfig
from dremio_mcp.utils.dremio_client import DremioClient
from fastmcp import FastMCP
# Import tool modules to register them
from dremio_mcp.tools import catalog, semantic, query, jobs, reflection, docs

@pytest.fixture(scope="session")
def dremio_client():
    """
    Fixture for Dremio Client configured via environment variable (default: cloud).
    Set DREMIO_TEST_PROFILE=software to test against software.
    """
    profile = os.environ.get("DREMIO_TEST_PROFILE", "cloud")
    print(f"\n--- Initializing Dremio Client with Profile: {profile} ---")
    try:
        config = DremioConfig(profile)
        client = DremioClient(config)
        return client
    except Exception as e:
        pytest.skip(f"Could not initialize {profile} client (check profiles.yaml): {e}")

@pytest.fixture(scope="session")
def mcp_server(dremio_client):
    """
    Fixture for FastMCP server with registered tools.
    """
    server = FastMCP("test_cloud")
    
    # Register all tools
    catalog.register(server, dremio_client)
    semantic.register(server, dremio_client)
    query.register(server, dremio_client)
    jobs.register(server, dremio_client)
    reflection.register(server, dremio_client)
    docs.register(server, dremio_client)
    
    return server

@pytest.fixture(scope="session")
def call_tool():
    """
    Helper to call a tool from the FastMCP server.
    """
    async def _call(server, name, args):
        tool = await server.get_tool(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")
            
        import inspect
        if inspect.iscoroutinefunction(tool.fn):
            return await tool.fn(**args)
        else:
            return tool.fn(**args)
            
    return _call

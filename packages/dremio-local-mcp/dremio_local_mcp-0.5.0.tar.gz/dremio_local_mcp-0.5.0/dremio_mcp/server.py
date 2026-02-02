from fastmcp import FastMCP
from dremio_mcp.config import DremioConfig
from dremio_mcp.utils.dremio_client import DremioClient

def create_server(config: DremioConfig) -> FastMCP:
    server = FastMCP("Dremio Local MCP")
    client = DremioClient(config)

    # Initialize tools here
    # We will import and register tools from the tools/ directory
    # Passing the client to them
    
    from dremio_mcp.tools import semantic, query, jobs, catalog, reflection, docs
    
    semantic.register(server, client)
    query.register(server, client)
    jobs.register(server, client)
    catalog.register(server, client)
    reflection.register(server, client)
    docs.register(server, client)
    
    from dremio_mcp import prompts
    prompts.register(server, client)

    return server

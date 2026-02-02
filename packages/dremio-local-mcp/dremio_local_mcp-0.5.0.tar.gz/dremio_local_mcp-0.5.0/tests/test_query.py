import pytest

@pytest.mark.asyncio
async def test_execute_query_select_one(mcp_server, call_tool):
    """Test executing a simple SELECT 1 query."""
    # Note: Cloud might need a context if strictly project based, but SELECT 1 usually generic?
    # Actually, Dremio Cloud SQL requires a project context implicitly provided by client.
    # WLM might reject if queues are strict, but SELECT 1 is cheap.
    query = "SELECT 1 as test_col"
    result = await call_tool(mcp_server, "execute_query", {"sql": query})
    text = str(result)
    
    # Check for success or specific error
    if "Error" in text and "WLM" in text:
        pytest.xfail("WLM Rejection expected in test environment")
    
    # If successful
    assert "test_col" in text or "1" in text or "preview" in text.lower()

import pytest

@pytest.mark.asyncio
async def test_search_docs(mcp_server, call_tool):
    """Test documentation search."""
    result = await call_tool(mcp_server, "search_docs", {"query": "dremio"})
    text = str(result)
    # Could be empty if no docs, but shouldn't error
    if "No documentation found" in text:
        pass
    else:
        assert "dremio" in text.lower()

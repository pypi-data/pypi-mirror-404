import pytest

@pytest.mark.asyncio
async def test_scan_reflections(mcp_server, call_tool):
    """Test scanning reflection opportunities."""
    result = await call_tool(mcp_server, "scan_reflection_opportunities", {})
    text = str(result)
    assert "Reflection Opportunity" in text

import pytest
import os

@pytest.mark.asyncio
async def test_plan_semantic_layer(mcp_server, tmp_path, call_tool):
    """Test semantic planning with mocked docs."""
    # Mock docs path via monkeypatching logic or just ensuring the tool runs
    # The tool looks in ~/dremiodocs.
    
    result = await call_tool(mcp_server, "plan_semantic_layer", {"goal": "Test Goal"})
    text = str(result)
    
    assert "Semantic Layer Plan" in text
    assert "Test Goal" in text
    assert "Gold" in text or "Silver" in text

@pytest.mark.asyncio
async def test_get_semantic_context_failure(mcp_server, call_tool):
    """Test semantic context on invalid path."""
    result = await call_tool(mcp_server, "get_semantic_context", {"path": "Invalid.Path"})
    text = str(result)
    assert "Error" in text or "null" in text

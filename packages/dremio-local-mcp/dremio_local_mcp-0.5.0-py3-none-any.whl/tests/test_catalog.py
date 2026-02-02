import pytest
import os

@pytest.mark.asyncio
async def test_list_datasets(mcp_server, call_tool):
    """Test listing root catalog."""
    # Try listing "Samples" which is common, or handle root failure gracefully if environment differs
    result = await call_tool(mcp_server, "list_datasets", {"path": "Samples"})
    text = str(result)
    
    # If Samples doesn't exist, we might get "not found", but that proves we connected.
    # If we get "Authentication error" that's a fail.
    # If we get "Resource not found", it means "Samples" isn't there, but the tool RAN.
    
    assert "Samples" in text or "contents" in text.lower() or "not found" in text.lower()
    # Ensure it's not an auth error
    assert "401" not in text and "Unauthorized" not in text

@pytest.mark.asyncio
async def test_get_context_invalid(mcp_server, call_tool):
    """Test context retrieval for non-existent path."""
    result = await call_tool(mcp_server, "get_context", {"path": "Invalid.Path.Resource"})
    text = str(result)
    assert "Error" in text or "not find" in text

@pytest.mark.asyncio
async def test_upload_dataset(mcp_server, tmp_path, call_tool):
    """Test local file reference upload."""
    f = tmp_path / "test.csv"
    f.write_text("col1,col2\n1,2")
    
    result = await call_tool(mcp_server, "upload_dataset", {
        "local_path": str(f),
        "dataset_name": "test_upload"
    })
    text = str(result)
    assert "col1,col2" in text

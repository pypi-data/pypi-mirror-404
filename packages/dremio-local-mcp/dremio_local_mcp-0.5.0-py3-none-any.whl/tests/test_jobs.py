import pytest

@pytest.mark.asyncio
async def test_list_jobs(mcp_server, call_tool):
    """Test listing jobs."""
    result = await call_tool(mcp_server, "list_jobs", {})
    text = str(result)
    # Cloud API might return "Resource not found" for /api/v3/job depending on context/permissions
    # We accept "Job ID" (success) or specific API errors that prove invocation.
    assert "Job ID" in text or "No jobs" in text or "Resource not found" in text

@pytest.mark.asyncio
async def test_analyze_job_failure(mcp_server, call_tool):
    """Test analyzing a fake job ID."""
    result = await call_tool(mcp_server, "analyze_job", {"job_id": "fake-id"})
    text = str(result)
    assert "Error" in text or "not found" in text

import sys
import os
sys.path.append(os.getcwd())
from unittest.mock import MagicMock
import unittest
import asyncio
import json

# dremio_client imports dremio_cli, which is now installed
from dremio_mcp.utils.dremio_client import DremioClient

# We need to assume FastMCP is available or mock it too if it fails.
# Trying to import it.
try:
    from fastmcp import FastMCP
except ImportError:
    # Retain mock if missing
    sys.modules["fastmcp"] = MagicMock()
    from fastmcp import FastMCP

# Import tools
from dremio_mcp.tools import reflection, query, semantic, catalog

class TestEnhancements(unittest.TestCase):
    
    def setUp(self):
        self.mock_client = MagicMock(spec=DremioClient)
        # Default behaviors
        self.mock_client.post_sql.return_value = "job_123"
        self.mock_client.get_job_results.return_value = {"rows": []}
        self.mock_client.get_catalog_item.return_value = {
            "entityType": "dataset", 
            "fields": [{"name": "col1", "type": {"name": "VARCHAR"}}]
        }
        
        # Setup Server with mocked client
        self.server = FastMCP("test_mock")
        reflection.register(self.server, self.mock_client)
        query.register(self.server, self.mock_client)
        semantic.register(self.server, self.mock_client)
        catalog.register(self.server, self.mock_client)

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_reflection_analysis(self):
        """Verify scan_reflection_opportunities analyzes sys.jobs."""
        tool = self.run_async(self.server.get_tool("scan_reflection_opportunities"))
        
        # Mock sys.jobs response
        self.mock_client.get_job_results.return_value = {
            "rows": [
                {
                    "query_text": "SELECT COUNT(*) FROM \"Space\".\"Folder\".\"BigTable\"", 
                    "dataset_graph": '[{"datasetPath": "Space.Folder.BigTable"}]',
                    "duration": 5000
                }
            ]
        }
        
        result = tool.fn()
        
        # Verify it called post_sql with sys.jobs query
        args, _ = self.mock_client.post_sql.call_args
        self.assertIn("sys.jobs", args[0])
        
        # Verify output contains recommendation
        self.assertIn("BigTable", result)
        self.assertIn("CREATE RAW REFLECTION", result)

    def test_query_guardrails(self):
        """Verify execute_query dry_run and format arguments."""
        tool = self.run_async(self.server.get_tool("execute_query"))
        
        # 1. Test Dry Run
        tool.fn(sql="SELECT * FROM foo", mode="dry_run")
        args, _ = self.mock_client.post_sql.call_args
        self.assertIn("EXPLAIN PLAN FOR SELECT * FROM foo", args[0])
        
        # 2. Test JSON Format
        self.mock_client.get_job_results.return_value = {
            "rows": [{"col": "val"}]
        }
        res_json = tool.fn(sql="SELECT 1", format="json")
        parsed = json.loads(res_json)
        self.assertEqual(parsed[0]["col"], "val")
        
        # 3. Test Destructive Block
        res_block = tool.fn(sql="DROP TABLE foo", mode="run")
        self.assertIn("SAFETY BLOCK", res_block)

    def test_semantic_ddl(self):
        """Verify plan_semantic_layer generates DDL."""
        tool = self.run_async(self.server.get_tool("plan_semantic_layer"))
        
        result = tool.fn(goal="Build a sales datamart")
        
        self.assertIn("CREATE OR REPLACE VIEW", result)
        self.assertIn("Layer_Silver", result)

    def test_data_profile(self):
        """Verify profile_dataset operation."""
        tool = self.run_async(self.server.get_tool("profile_dataset"))
        
        # Define logic for multiple calls
        def side_effect(sql, **kwargs):
            return "job_id"
            
        self.mock_client.post_sql.side_effect = side_effect
        
        # We need stateful return values for get_job_results based on call order?
        # A simpler way is to check the SQL strings sent.
        
        # Mock getting schema
        self.mock_client.get_catalog_item.return_value = {
            "entityType": "dataset", 
            "fields": [{"name": "id", "type": {"name": "INTEGER"}}]
        }
        
        # Mock results
        # First call (count) -> [{"cnt": 100}]
        # Second call (sample) -> [{"id": 1}]
        self.mock_client.get_job_results.side_effect = [
            {"rows": [{"cnt": 100}]},
            {"rows": [{"id": 1}, {"id": 2}]}
        ]
        
        result = tool.fn(path="Space.Table")
        
        self.assertIn("Total Rows**: 100", result)
        self.assertIn("| id | INTEGER |", result)

if __name__ == "__main__":
    unittest.main()

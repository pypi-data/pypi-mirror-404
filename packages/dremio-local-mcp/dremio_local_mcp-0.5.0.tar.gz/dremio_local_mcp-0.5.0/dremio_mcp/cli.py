import argparse
import sys
import json
from dremio_mcp.config import DremioConfig
from dremio_mcp.server import create_server
from dremio_mcp.utils.dremio_client import DremioClient

def main():
    parser = argparse.ArgumentParser(description="Dremio MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Start Command
    start_parser = subparsers.add_parser("start", help="Start the MCP server")
    start_parser.add_argument("--profile", default="default", help="Dremio profile name")

    # Config Command
    config_parser = subparsers.add_parser("config", help="Generate MCP configuration")
    config_parser.add_argument("--profile", default="default", help="Dremio profile name")

    # Test Command
    test_parser = subparsers.add_parser("test", help="Test connectivity")
    test_parser.add_argument("--profile", default="default", help="Dremio profile name")

    args = parser.parse_args()

    if args.command == "start":
        # Initialize and run the server
        try:
            config = DremioConfig(args.profile)
            server = create_server(config)
            server.run(transport="stdio")
        except Exception as e:
            print(f"Error starting server: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "config":
        try:
            # Check if profile works before printing config
            DremioConfig(args.profile)
            
            # Print configuration for reuse
            cmd_path = sys.argv[0]
            if not cmd_path.endswith("dremio-local-mcp"):
                cmd_path = "dremio-local-mcp" # Default assumption if running via python

            config_json = {
                "mcpServers": {
                    "dremio": {
                        "command": "dremio-local-mcp",
                        "args": ["start", "--profile", args.profile]
                    }
                }
            }
            print(json.dumps(config_json, indent=2))
        except Exception as e:
             print(f"Error generating config: {e}", file=sys.stderr)
             sys.exit(1)

    elif args.command == "test":
        try:
            config = DremioConfig(args.profile)
            client = DremioClient(config)
            # Access base_url from the underlying dremio_cli client
            base_url = getattr(client.client, "base_url", "Dremio")
            print(f"Connecting to {base_url} as {args.profile}...")
            
            # Simple SQL test
            job_id = client.post_sql("SELECT 1")
            client.wait_for_job(job_id)
            print("✅ Connectivity Test Passed: SELECT 1 executed successfully.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Connectivity Test Failed: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

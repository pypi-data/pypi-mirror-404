# Project Overview `dremio-local-mcp`

[Full Documentation on Git Repo Here](https://github.com/AlexMercedCoder/dremio-local-mcp)

The `dremio-local-mcp` is a Model Context Protocol (MCP) server that connects AI assistants (like Claude) to your Dremio lakehouse.

## Features
- **Semantic Layer Management**: Create views, update wikis, and tag datasets directly from chat.
- **Data Exploration**: List datasets, inspect schemas, and package context for analysis.
- **Query Execution**: Run SQL queries safely (destructive queries require confirmation).
- **Job Analysis**: Analyze job profiles for performance improvements.

## Installation

```bash
pip install dremio-local-mcp
```

## Configuration

This tool uses the standard Dremio CLI configuration format. You can manage your Dremio credentials using the **dremio-cli** utility (recommended) or manually via a YAML file.

### Option 1: Using dremio-cli

First, install the CLI (if not already present):
```bash
pip install dremio-cli
```

Then create a profile for your environment:

**For Dremio Cloud:**
```bash
# Create a profile named 'default'
dremio profile create --name default --type cloud --token <your-pat-token> --project-id <your-project-id> --base-url https://api.dremio.cloud
```

**For Dremio Software:**
```bash
# Create a profile named 'software'
dremio profile create --name software --type software --base-url http://localhost:9047 --username <user> --password <pass>
```
*(For Software, `verify_ssl` defaults to `true`. Add `--no-verify-ssl` if using self-signed certs)*

### Option 2: Manual YAML

Create or edit `~/.dremio/profiles.yaml` manually:

```yaml
default_profile: cloud
profiles:
  cloud:
    base_url: "https://api.dremio.cloud"
    token: "your-pat-token"
    project_id: "your-project-id"
    verify_ssl: true
  software:
    base_url: "http://localhost:9047"
    username: "admin"
    password: "password123"
    verify_ssl: false

### Supported Authentication Flows

This MCP server supports all authentication flows available in `dremio-cli` (v1.10.0+):

1.  **Cloud (PAT)**: Requires `token` and `project_id`.
2.  **Software (PAT)**: Requires `token` and `base_url`.
3.  **Software (User/Pass)**: Requires `username`, `password`, and `base_url`.
4.  **Service (OAuth2 Credentials)**: Requires `client_id`, `client_secret`, and `base_url`.

> [!TIP]
> **Service/Credentials Flow**: If you are using the Client Credentials flow (common for service accounts), it is recommended to explicitly set the scope in your profile to ensure full access.
>
> ```yaml
> service_profile:
>   type: "software" # or "cloud"
>   base_url: "https://dremio.org/api/v3"
>   auth:
>     type: "oauth"
>     client_id: "your-client-id"
>     client_secret: "your-client-secret"
>     # scope: "dremio.all" # NOTE: dremio-cli v1.11.0 currently ignores this key and defaults to dremio.all on retry
> ```
```

## Usage

### Start the Server

```bash
dremio-local-mcp start --profile default
```

### Connectivity Test

```bash
dremio-local-mcp test --profile default
```

### Claude Desktop Config

Generate the configuration block:

```bash
dremio-local-mcp config --profile default
```

Copy the output into your `claude_desktop_config.json`.

## Documentation
- [CLI Commands](docs/cli/README.md)
- [Tools Reference](docs/tools/README.md)
- [Prompts Reference](docs/prompts/README.md)
- [Client Configuration](docs/clients.md)

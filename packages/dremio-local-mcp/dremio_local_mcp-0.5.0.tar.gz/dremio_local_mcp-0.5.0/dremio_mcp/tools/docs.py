from fastmcp import FastMCP
from dremio_mcp.utils.dremio_client import DremioClient
import os
from pathlib import Path

def register(server: FastMCP, client: DremioClient):
    
    @server.tool()
    def search_docs(query: str) -> str:
        """
        Search the local `dremiodocs` documentation.
        This searches for markdown files in the `dremiodocs` folder relative to the current working directory.
        """
        try:
            # Locate docs folder
            # Try CWD first
            cwd = Path.cwd()
            docs_path = cwd / "dremiodocs"
            
            if not docs_path.exists():
                # Fallback: Check if we are inside the structure?
                # Or just return path not found.
                return f"Error: `dremiodocs` folder not found at {docs_path}. Please run this from the project root."
            
            # recursive grep-like search
            results = []
            query_lower = query.lower()
            
            for root, _, files in os.walk(docs_path):
                for file in files:
                    if file.endswith(".md"):
                        path = Path(root) / file
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if query_lower in content.lower():
                                    # Found match, snippet it
                                    # Simple snippet
                                    idx = content.lower().find(query_lower)
                                    start = max(0, idx - 50)
                                    end = min(len(content), idx + 200)
                                    snippet = content[start:end].replace("\n", " ")
                                    rel_path = path.relative_to(cwd)
                                    results.append(f"**{rel_path}**:\n...{snippet}...")
                        except Exception as read_err:
                            results.append(f"Error reading {file}: {read_err}")
            
            if not results:
                return f"No results found for '{query}' in `dremiodocs`."
            
            return "\n\n".join(results[:10]) # Limit to top 10 files

        except Exception as e:
            return f"Error searching docs: {e}"

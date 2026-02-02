import os
from typing import List

DOCS_PATH = os.path.expanduser("~/dremiodocs")

def query_docs(query: str, limit: int = 3) -> str:
    """
    Internal helper to search local dremiodocs.
    """
    if not os.path.exists(DOCS_PATH):
        return ""
        
    results = []
    # Simple keyword match
    query_lower = query.lower()
    
    for root, _, files in os.walk(DOCS_PATH):
        for file in files:
            if file.endswith(".md"):
                try:
                    path = os.path.join(root, file)
                    with open(path, "r") as f:
                        content = f.read()
                        if query_lower in content.lower():
                            # Snippet
                            idx = content.lower().find(query_lower)
                            start = max(0, idx - 100)
                            end = min(len(content), idx + 300)
                            snippet = content[start:end].replace("\n", " ")
                            results.append(f"- **{file}**: ...{snippet}...")
                            if len(results) >= limit:
                                break
                except:
                    continue
        if len(results) >= limit:
            break
            
    if results:
         return "\nRelevant Documentation Found:\n" + "\n".join(results)
    return ""

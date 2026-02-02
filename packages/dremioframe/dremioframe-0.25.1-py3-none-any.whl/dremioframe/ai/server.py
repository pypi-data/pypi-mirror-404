try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise ImportError("The 'mcp' package is required for the MCP server. Install with `pip install dremioframe[server]`")

from dremioframe.client import DremioClient
import os
import json

# Initialize FastMCP server
mcp = FastMCP("Dremio Agent")

# Initialize Dremio Client and Agent lazily or globally?
# We need environment variables to be set.
# Let's assume they are set in the environment where the server runs.

def get_client():
    # Check for required env vars
    if not os.getenv("DREMIO_PAT") and not (os.getenv("DREMIO_SOFTWARE_USER") and os.getenv("DREMIO_SOFTWARE_PASSWORD")):
        # Try to load from .env if not present
        from dotenv import load_dotenv
        load_dotenv()
        
    # Determine mode
    mode = "cloud"
    if os.getenv("DREMIO_SOFTWARE_HOST"):
        mode = "v26" # Default to v26 for software if host is present
        
    try:
        client = DremioClient(mode=mode)
        # We need an LLM for the agent. 
        # The agent usually takes an LLM object.
        # But for MCP, we might just want to expose the TOOLS, not the agent's reasoning loop?
        # The MCP Client (Claude) IS the agent. We just provide tools.
        # So we don't need DremioAgent class necessarily, just the tools it uses.
        # However, DremioAgent has methods that CREATE tools.
        
        # Let's look at DremioAgent to see how it defines tools.
        # It likely has a method `get_tools()`.
        return client
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Dremio Client: {e}")

# We will define tools directly on the FastMCP server, delegating to DremioClient.

@mcp.tool()
def list_catalog(path: str = None) -> str:
    """
    List the contents of the Dremio catalog.
    
    Args:
        path: Optional path to list (e.g. "Space.Folder"). If None, lists root.
    """
    client = get_client()
    try:
        items = client.catalog.list_catalog(path)
        return json.dumps(items, indent=2)
    except Exception as e:
        return f"Error listing catalog: {e}"

@mcp.tool()
def get_entity(path: str) -> str:
    """
    Get details of a specific catalog entity (dataset, folder, source).
    
    Args:
        path: The full path of the entity (e.g. "Space.Folder.Table").
    """
    client = get_client()
    try:
        entity = client.catalog.get_entity(path)
        return json.dumps(entity, indent=2)
    except Exception as e:
        return f"Error getting entity: {e}"

@mcp.tool()
def query_dremio(sql: str) -> str:
    """
    Execute a SQL query against Dremio and return the results.
    
    Args:
        sql: The SQL query to execute.
    """
    client = get_client()
    try:
        # Use pandas for easy serialization
        df = client.query(sql, format="pandas")
        if df.empty:
            return "Query returned no results."
        return df.to_json(orient="records", date_format="iso")
    except Exception as e:
        return f"Error executing query: {e}"

@mcp.tool()
def list_reflections() -> str:
    """
    List all reflections in Dremio.
    """
    client = get_client()
    try:
        reflections = client.admin.list_reflections()
        return json.dumps(reflections, indent=2)
    except Exception as e:
        return f"Error listing reflections: {e}"

@mcp.tool()
def get_job_profile(job_id: str) -> str:
    """
    Get the profile/details of a specific job.
    
    Args:
        job_id: The Job ID.
    """
    client = get_client()
    try:
        profile = client.admin.get_job_profile(job_id)
        # profile is a QueryProfile object, need to serialize
        return json.dumps(profile.data, indent=2)
    except Exception as e:
        return f"Error getting job profile: {e}"

@mcp.tool()
def create_view(path: str, sql: str) -> str:
    """
    Create a new View (Virtual Dataset).
    
    Args:
        path: The full path for the new view (e.g. "Space.Folder.NewView").
        sql: The SQL definition of the view.
    """
    client = get_client()
    try:
        # Parse path into list
        path_list = path.split(".")
        # Remove quotes if present
        path_list = [p.strip('"') for p in path_list]
        
        result = client.catalog.create_view(path_list, sql)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error creating view: {e}"

# --- Resources (Documentation) ---

@mcp.resource("dremio://docs/{category}/{file}")
def read_library_doc(category: str, file: str) -> str:
    """Read a dremioframe library documentation file."""
    # Construct path: docs/{category}/{file}
    # Security check: prevent traversal
    if ".." in category or ".." in file:
        raise ValueError("Invalid path")
        
    base_path = os.path.join(os.getcwd(), "docs")
    # Handle root docs (category might be empty or special?)
    # The URI pattern enforces category. 
    # Let's handle root docs via a separate resource or assume they are in a 'root' category if we restructure?
    # Or we can just list them.
    
    full_path = os.path.join(base_path, category, file)
    if not os.path.exists(full_path):
        return "File not found."
        
    with open(full_path, "r") as f:
        return f.read()

@mcp.resource("dremio://dremiodocs/{category}/{file}")
def read_dremio_doc(category: str, file: str) -> str:
    """Read a Dremio native documentation file."""
    if ".." in category or ".." in file:
        raise ValueError("Invalid path")
        
    base_path = os.path.join(os.getcwd(), "dremiodocs")
    full_path = os.path.join(base_path, category, file)
    if not os.path.exists(full_path):
        return "File not found."
        
    with open(full_path, "r") as f:
        return f.read()

# We can also dynamically list resources if FastMCP supports it easily via a generator
# FastMCP doesn't have a simple decorator for *listing* all resources dynamically in the same way as tools
# usually you define static resources or use a regex pattern (which we did).
# But clients need to discover them.
# FastMCP handles discovery for regex resources by... well, it doesn't list *all* possible matches automatically.
# We might need to implement a 'list_resources' tool or rely on the client knowing the URIs?
# Wait, the MCP spec allows listing resources. FastMCP might expose a way to register a lister.
# Looking at FastMCP docs (simulated): usually you pass a list or a function.
# Let's try to add a startup hook or just rely on tools for discovery if resources are hard to list dynamically in this wrapper.
# BUT, the user asked for "visibility to the library docs".
# Providing a tool `list_documentation` is good (which we have in agent).
# Let's expose `list_documentation` as a tool too, which returns the paths.
# Then the user can read them via the resource URI or a tool.
# Actually, let's just add `list_docs` tool that returns the URIs.

@mcp.tool()
def list_available_docs() -> str:
    """List available documentation URIs."""
    docs = []
    
    # Library docs
    docs_path = os.path.join(os.getcwd(), "docs")
    if os.path.exists(docs_path):
        for root, _, files in os.walk(docs_path):
            for file in files:
                if file.endswith(".md"):
                    rel_path = os.path.relpath(os.path.join(root, file), docs_path)
                    # rel_path might be "category/file.md" or "file.md"
                    # Our resource pattern is dremio://docs/{category}/{file}
                    # If it's in root, it won't match {category}/{file} easily unless we adjust pattern.
                    # Let's just return the path for now.
                    docs.append(f"Library: {rel_path}")

    # Dremio docs
    dremio_docs_path = os.path.join(os.getcwd(), "dremiodocs")
    if os.path.exists(dremio_docs_path):
        for root, _, files in os.walk(dremio_docs_path):
            for file in files:
                if file.endswith(".md"):
                    rel_path = os.path.relpath(os.path.join(root, file), dremio_docs_path)
                    docs.append(f"Dremio: {rel_path}")
                    
    return "\n".join(docs)

def serve():
    """Run the MCP server."""
    mcp.run()

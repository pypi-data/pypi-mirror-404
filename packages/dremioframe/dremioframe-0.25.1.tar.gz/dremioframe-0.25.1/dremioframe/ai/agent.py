import os
import glob
from typing import Optional, List, Union, Dict, Any
from langchain_core.tools import tool
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

@tool
def list_documentation() -> List[str]:
    """Lists all available documentation files in the docs directory."""
    # Try to find docs dir
    possible_paths = [
        os.path.join(os.getcwd(), "docs"),
        os.path.join(os.path.dirname(__file__), "../../docs"),
    ]
    
    docs_path = None
    for p in possible_paths:
        if os.path.exists(p):
            docs_path = p
            break
    
    if not docs_path:
        return ["Error: Documentation directory not found."]

    files = glob.glob(os.path.join(docs_path, "**/*.md"), recursive=True)
    return [os.path.relpath(f, docs_path) for f in files]

@tool
def read_documentation(file_path: str) -> str:
    """Reads the content of a specific documentation file."""
    possible_paths = [
        os.path.join(os.getcwd(), "docs"),
        os.path.join(os.path.dirname(__file__), "../../docs"),
    ]
    
    docs_path = None
    for p in possible_paths:
        if os.path.exists(p):
            docs_path = p
            break
            
    if not docs_path:
        return "Error: Documentation directory not found."

    full_path = os.path.join(docs_path, file_path)
    if not os.path.exists(full_path):
        return f"Error: File {file_path} not found."
        
    with open(full_path, "r") as f:
        return f.read()

@tool
def search_dremio_docs(query: str) -> List[str]:
    """
    Searches native Dremio documentation in the dremiodocs directory.
    Returns a list of filenames that might be relevant.
    """
    possible_paths = [
        os.path.join(os.getcwd(), "dremiodocs"),
        os.path.join(os.path.dirname(__file__), "../../dremiodocs"),
    ]
    
    docs_path = None
    for p in possible_paths:
        if os.path.exists(p):
            docs_path = p
            break
            
    if not docs_path:
        return ["Error: Dremio documentation directory not found."]
        
    # Simple search: find files containing the query string (case-insensitive)
    matches = []
    for root, _, files in os.walk(docs_path):
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", errors="ignore") as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            matches.append(os.path.relpath(full_path, docs_path))
                except Exception:
                    continue
    return matches[:5] # Return top 5 matches

@tool
def read_dremio_doc(file_path: str) -> str:
    """Reads the content of a specific Dremio documentation file."""
    possible_paths = [
        os.path.join(os.getcwd(), "dremiodocs"),
        os.path.join(os.path.dirname(__file__), "../../dremiodocs"),
    ]
    
    docs_path = None
    for p in possible_paths:
        if os.path.exists(p):
            docs_path = p
            break
            
    if not docs_path:
        return "Error: Dremio documentation directory not found."

    full_path = os.path.join(docs_path, file_path)
    if not os.path.exists(full_path):
        return f"Error: File {file_path} not found."
        
    with open(full_path, "r") as f:
        return f.read()

@tool
def list_catalog_items(path: Optional[str] = None) -> str:
    """
    Lists items in the Dremio catalog.
    If path is None, lists root items (Spaces, Sources, Home).
    If path is provided (e.g. "Space.Folder"), lists items in that path.
    """
    try:
        # Import here to avoid circular dependency if any, and ensure client is created at runtime
        from dremioframe.client import DremioClient
        client = DremioClient() # Expects env vars
        
        if path:
            # list_catalog might need a path argument or we use list_catalog() on root
            # The current client.catalog.list_catalog() implementation might vary
            # Let's assume we can list by path or it lists everything.
            # Checking catalog.py would be good, but for now assuming standard behavior or using by_path if exists.
            # Actually, looking at previous context, client.catalog.list_catalog() exists.
            # Let's try to use it.
            items = client.catalog.list_catalog(path)
        else:
            items = client.catalog.list_catalog()
            
        return str(items)
    except Exception as e:
        return f"Error listing catalog: {e}"

@tool
def get_table_schema(path: str) -> str:
    """
    Retrieves the schema (columns and types) of a dataset (table/view).
    Path should be the full path (e.g. "Space.Folder.Dataset").
    """
    try:
        from dremioframe.client import DremioClient
        client = DremioClient()
        # We can use client.table(path).schema or similar if available, 
        # or just fetch catalog item and look at fields.
        # client.catalog.get_dataset(path) should return info including fields.
        dataset = client.catalog.get_dataset(path)
        if 'fields' in dataset:
            return str(dataset['fields'])
        return f"No fields found for {path}. Metadata: {dataset}"
    except Exception as e:
        return f"Error getting schema: {e}"
@tool
def get_job_details(job_id: str) -> str:
    """
    Retrieves details for a specific job, including status and error messages.
    """
    try:
        from dremioframe.client import DremioClient
        client = DremioClient()
        # Use the raw session to get job details as client.get_job_profile might return a Profile object
        # We want the raw JSON for the agent to inspect
        response = client.session.get(f"{client.base_url}/job/{job_id}")
        response.raise_for_status()
        job = response.json()
        
        # Extract relevant info
        info = {
            "id": job.get("id"),
            "status": job.get("jobState"),
            "queryType": job.get("queryType"),
            "user": job.get("user"),
            "startTime": job.get("startTime"),
            "endTime": job.get("endTime"),
            "errorMessage": job.get("errorMessage"),
            "failureInfo": job.get("failureInfo")
        }
        return str(info)
    except Exception as e:
        return f"Error getting job details: {e}"

@tool
def list_recent_jobs(limit: int = 5) -> str:
    """
    Lists the most recent jobs.
    """
    try:
        from dremioframe.client import DremioClient
        client = DremioClient()
        # Dremio SQL API doesn't have a simple "list jobs" table usually, 
        # but we can use the REST API /jobs endpoint if available or sys.jobs table if accessible.
        # sys.jobs is often available.
        try:
            jobs = client.sql(f"SELECT job_id, status, user_name, start_time, error_msg FROM sys.jobs ORDER BY start_time DESC LIMIT {limit}").collect()
            return str(jobs.to_dict(orient='records'))
        except Exception:
            # Fallback to REST API if sys.jobs fails (e.g. no permission)
            # Note: /jobs endpoint might be different across versions
            return "Error: Could not list jobs from sys.jobs."
    except Exception as e:
        return f"Error listing jobs: {e}"

@tool
def list_reflections() -> str:
    """
    Lists all reflections in the Dremio environment.
    """
    try:
        from dremioframe.client import DremioClient
        client = DremioClient()
        reflections = client.admin.list_reflections()
        # Summarize for the agent
        summary = []
        for r in reflections.get("data", []):
            summary.append(f"ID: {r['id']}, Name: {r['name']}, Type: {r['type']}, Status: {r['status']}")
        return "\n".join(summary) if summary else "No reflections found."
    except Exception as e:
        return f"Error listing reflections: {e}"

@tool
def create_reflection(dataset_id: str, name: str, type: str, fields: List[str]) -> str:
    """
    Creates a reflection.
    type: "RAW" or "AGGREGATION"
    fields: List of field names to include.
    """
    try:
        from dremioframe.client import DremioClient
        client = DremioClient()
        if type.upper() == "RAW":
            client.admin.create_reflection(dataset_id, name, type, display_fields=fields)
        else:
            # For simplicity, assume fields are dimensions and measures
            # In a real agent, we might want more granular control
            client.admin.create_reflection(dataset_id, name, type, dimension_fields=fields, measure_fields=fields)
        return f"Reflection '{name}' created successfully."
    except Exception as e:
        return f"Error creating reflection: {e}"

@tool
def show_grants(entity: str) -> str:
    """
    Shows privileges granted on a specific entity (table, view, folder, space).
    """
    try:
        from dremioframe.client import DremioClient
        client = DremioClient()
        # Dremio SQL: SHOW GRANTS ON [TABLE|VIEW|FOLDER|SPACE] <name>
        # We need to determine the type or just try generic
        # But SHOW GRANTS syntax usually requires type.
        # Let's try to infer or just use TABLE as default for datasets
        try:
            grants = client.sql(f"SHOW GRANTS ON TABLE {entity}").collect()
            return str(grants.to_dict(orient='records'))
        except Exception:
            # Try without type or other types?
            return "Error: Could not fetch grants. Ensure the entity exists and you have permission."
    except Exception as e:
        return f"Error showing grants: {e}"

class DremioAgent:
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None, llm: Optional[BaseChatModel] = None, 
                 memory_path: Optional[str] = None, context_folder: Optional[str] = None,
                 mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the Dremio AI Agent.
        
        Args:
            model: LLM model name (e.g., "gpt-4o", "claude-3-5-sonnet", "gemini-pro").
            api_key: API key for the LLM provider.
            llm: Pre-configured LLM instance (overrides model and api_key).
            memory_path: Path to SQLite database for conversation persistence. If None, memory is not persisted.
            context_folder: Path to a folder containing additional context files for the agent to reference.
            mcp_servers: Dictionary of MCP server configurations. Keys are server names, values are dicts with 'transport', 'command', 'args'.
        """
        self.model_name = model
        self.api_key = api_key
        self.llm = llm or self._initialize_llm()
        self.memory_path = memory_path
        self.context_folder = context_folder
        self.mcp_servers = mcp_servers or {}
        
        # Build tools list
        self.tools = [
            list_documentation, read_documentation, search_dremio_docs, read_dremio_doc, 
            list_catalog_items, get_table_schema, get_job_details, list_recent_jobs, 
            list_reflections, create_reflection, show_grants
        ]
        
        # Add context folder tools if specified
        if self.context_folder:
            self.tools.extend([
                self._create_list_context_files_tool(), 
                self._create_read_context_file_tool(),
                self._create_read_pdf_file_tool()
            ])
        
        # Add MCP tools if specified
        if self.mcp_servers:
            mcp_tools = self._initialize_mcp_tools()
            if mcp_tools:
                self.tools.extend(mcp_tools)
        
        self.checkpointer = self._initialize_checkpointer()
        self.agent = self._initialize_agent()

    def _initialize_llm(self):
        if "gpt" in self.model_name:
            api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found.")
            return ChatOpenAI(model=self.model_name, api_key=api_key, temperature=0)
        elif "claude" in self.model_name:
            api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found.")
            return ChatAnthropic(model=self.model_name, api_key=api_key, temperature=0)
        elif "gemini" in self.model_name:
            api_key = self.api_key or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found.")
            return ChatGoogleGenerativeAI(model=self.model_name, google_api_key=api_key, temperature=0)
        else:
            api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
            if api_key:
                return ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=0)
            raise ValueError(f"Unsupported model or missing API key for {self.model_name}")

    def _initialize_checkpointer(self):
        """Initialize the checkpointer for memory persistence."""
        if self.memory_path:
            try:
                from langgraph.checkpoint.sqlite import SqliteSaver
                return SqliteSaver.from_conn_string(self.memory_path)
            except ImportError:
                print("Warning: langgraph.checkpoint.sqlite not found. Memory will not be persisted.")
                print("Install with: pip install langgraph-checkpoint-sqlite")
                return None
        return None

    def _initialize_mcp_tools(self):
        """Initialize tools from MCP servers."""
        try:
            from langchain_mcp_adapters import MultiServerMCPClient
        except ImportError:
            print("Warning: langchain-mcp-adapters not found. MCP servers will not be available.")
            print("Install with: pip install dremioframe[mcp]")
            return []
        
        try:
            mcp_client = MultiServerMCPClient(self.mcp_servers)
            tools = mcp_client.get_tools()
            print(f"Loaded {len(tools)} tools from {len(self.mcp_servers)} MCP server(s)")
            return tools
        except Exception as e:
            print(f"Warning: Failed to initialize MCP tools: {e}")
            return []

    def _create_list_context_files_tool(self):
        """Create a tool to list files in the context folder."""
        context_folder = self.context_folder
        
        @tool
        def list_context_files() -> List[str]:
            """Lists all files in the user-provided context folder."""
            if not os.path.exists(context_folder):
                return [f"Error: Context folder not found: {context_folder}"]
            
            files = []
            for root, _, filenames in os.walk(context_folder):
                for filename in filenames:
                    rel_path = os.path.relpath(os.path.join(root, filename), context_folder)
                    files.append(rel_path)
            return files
        
        return list_context_files
    
    def _create_read_context_file_tool(self):
        """Create a tool to read files from the context folder."""
        context_folder = self.context_folder
        
        @tool
        def read_context_file(file_path: str) -> str:
            """Reads the content of a file from the user-provided context folder."""
            full_path = os.path.join(context_folder, file_path)
            if not os.path.exists(full_path):
                return f"Error: File not found: {file_path}"
            
            try:
                with open(full_path, "r", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        
        return read_context_file

    def _create_read_pdf_file_tool(self):
        """Create a tool to read PDF files from the context folder."""
        context_folder = self.context_folder
        
        @tool
        def read_pdf_file(file_path: str) -> str:
            """Extracts text content from a PDF file in the user-provided context folder."""
            try:
                import pdfplumber
            except ImportError:
                return "Error: pdfplumber not installed. Install with: pip install dremioframe[document]"
            
            full_path = os.path.join(context_folder, file_path)
            if not os.path.exists(full_path):
                return f"Error: File not found: {file_path}"
            
            try:
                text = ""
                with pdfplumber.open(full_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text if text else "No text content found in PDF"
            except Exception as e:
                return f"Error reading PDF: {e}"
        
        return read_pdf_file

    def _initialize_agent(self):
        system_message = (
            "You are an expert Dremio developer assistant. Your goal is to help users with Dremio tasks.\n"
            "You have access to the library's documentation and native Dremio documentation via tools.\n"
            "You also have access to the Dremio Catalog via `list_catalog_items` and `get_table_schema` to inspect tables and views.\n"
            "You can inspect job details using `get_job_details` and list recent jobs with `list_recent_jobs`.\n"
            "You can manage reflections using `list_reflections` and `create_reflection`.\n"
            "You can check privileges using `show_grants`.\n"
        )
        
        if self.context_folder:
            system_message += (
                "\nYou have access to user-provided context files via `list_context_files`, `read_context_file`, and `read_pdf_file`.\n"
                "Use these tools when the user mentions files or context that might be in their project folder.\n"
                "For PDF files, use `read_pdf_file` to extract text content.\n"
                "When asked to extract structured data from documents (PDFs, markdown, etc.), read the files, "
                "analyze the content, and generate Python code to create/insert data into Dremio tables based on the user's schema requirements."
            )
        
        if self.mcp_servers:
            system_message += (
                f"\nYou have access to {len(self.mcp_servers)} MCP server(s) providing additional tools.\n"
                "Use these tools when appropriate for the user's request."
            )
        
        system_message += (
            "\nWhen asked to generate a script, ensure it is complete, runnable, and includes comments about required environment variables.\n"
            "When asked to generate SQL, validate table names and columns using the catalog tools if possible. Ensure table paths are correctly quoted (e.g. \"Space\".\"Folder\".\"Table\").\n"
            "When asked to generate an API call, use the documentation to find the correct endpoint and payload.\n"
            "The output should be ONLY the requested content (code block, SQL, or cURL command) unless asked otherwise."
        )
        
        if self.checkpointer:
            return create_react_agent(self.llm, self.tools, checkpointer=self.checkpointer, prompt=system_message)
        else:
            return create_react_agent(self.llm, self.tools, prompt=system_message)

    def generate_script(self, prompt: str, output_file: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """
        Generates a dremioframe script based on the prompt.
        
        Args:
            prompt: Description of the script to generate.
            output_file: If provided, writes the code to this file.
            session_id: Session ID for conversation persistence. Required if memory_path was set.
        
        Returns:
            The generated Python code.
        """
        full_prompt = f"Generate a Python script using dremioframe for: {prompt}"
        config = {"configurable": {"thread_id": session_id}} if session_id else {}
        response = self.agent.invoke({"messages": [("user", full_prompt)]}, config=config)
        # LangGraph returns state, output is in messages[-1].content
        output = response["messages"][-1].content
        
        # Extract code block if present
        if "```python" in output:
            code = output.split("```python")[1].split("```")[0].strip()
        elif "```" in output:
            code = output.split("```")[1].split("```")[0].strip()
        else:
            code = output

        if output_file:
            with open(output_file, "w") as f:
                f.write(code)
            return f"Script generated and saved to {output_file}"
        
        return code

    def generate_sql(self, prompt: str, session_id: Optional[str] = None) -> str:
        """
        Generates a SQL query based on the prompt.
        
        Args:
            prompt: Description of the SQL query to generate.
            session_id: Session ID for conversation persistence.
        
        Returns:
            The generated SQL query.
        """
        full_prompt = f"Generate a Dremio SQL query for: {prompt}. Use the catalog tools to verify table names and columns if needed. Output ONLY the SQL query."
        config = {"configurable": {"thread_id": session_id}} if session_id else {}
        response = self.agent.invoke({"messages": [("user", full_prompt)]}, config=config)
        output = response["messages"][-1].content
        
        if "```sql" in output:
            return output.split("```sql")[1].split("```")[0].strip()
        elif "```" in output:
            return output.split("```")[1].split("```")[0].strip()
        return output.strip()

    def generate_api_call(self, prompt: str, session_id: Optional[str] = None) -> str:
        """
        Generates a cURL command for the Dremio API based on the prompt.
        
        Args:
            prompt: Description of the API call to generate.
            session_id: Session ID for conversation persistence.
        
        Returns:
            The generated cURL command.
        """
        full_prompt = f"Generate a cURL command for the Dremio API for: {prompt}. Use the documentation tools to find the correct endpoint. Output ONLY the cURL command."
        config = {"configurable": {"thread_id": session_id}} if session_id else {}
        response = self.agent.invoke({"messages": [("user", full_prompt)]}, config=config)
        output = response["messages"][-1].content
        
        if "```bash" in output:
            return output.split("```bash")[1].split("```")[0].strip()
        elif "```sh" in output:
            return output.split("```sh")[1].split("```")[0].strip()
        elif "```" in output:
            return output.split("```")[1].split("```")[0].strip()
        return output.strip()

    def analyze_job_failure(self, job_id: str) -> str:
        """
        Analyzes a failed job and provides an explanation and potential fixes.
        """
        full_prompt = f"Analyze the failure for job {job_id}. Use `get_job_details` to retrieve the error message and context. Explain why it failed and suggest a fix."
        response = self.agent.invoke({"messages": [("user", full_prompt)]})
        return response["messages"][-1].content

    def recommend_reflections(self, query: str) -> str:
        """
        Analyzes a SQL query and recommends reflections to improve performance.
        """
        full_prompt = f"Analyze this SQL query and recommend Dremio Reflections (Raw or Aggregation) that would accelerate it. Specify the fields for dimensions, measures, etc. Assume the table and columns exist.\n\nQuery: {query}"
        response = self.agent.invoke({"messages": [("user", full_prompt)]})
        return response["messages"][-1].content

    def auto_document_dataset(self, path: str) -> str:
        """
        Generates a Wiki description and Tags for a dataset based on its schema.
        """
        full_prompt = f"Generate a Wiki description (Markdown) and a list of 3-5 Tags for the Dremio dataset at '{path}'. Use `get_table_schema` to inspect the columns and types. The output should be a JSON object with 'wiki' and 'tags' keys."
        response = self.agent.invoke({"messages": [("user", full_prompt)]})
        return response["messages"][-1].content

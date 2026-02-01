import os
import requests
from typing import Union, Dict, Any
from .catalog import Catalog
from .builder import DremioBuilder
from .admin import Admin
from .udf import UDFManager
from .utils import get_env_var

class DremioClient:
    def __init__(self, pat: str = None, project_id: str = None, base_url: str = None,
                 hostname: str = "data.dremio.cloud", port: int = None,
                 username: str = None, password: str = None, tls: bool = True,
                 disable_certificate_verification: bool = False,
                 flight_port: int = None, flight_endpoint: str = None,
                 mode: str = "cloud",
                 client_id: str = None, client_secret: str = None,
                 profile: str = None):
        """
        Initialize Dremio Client.
        
        Args:
            pat: Personal Access Token (for Cloud or Software v26+)
            project_id: Project ID (Cloud only, set to None for Software)
            base_url: Custom base URL (auto-detected if not provided)
            hostname: Dremio hostname
            port: REST API port (auto-detected based on mode if not provided)
            username: Username for authentication (Software with user/pass)
            password: Password for authentication (Software with user/pass)
            tls: Enable TLS/SSL
            disable_certificate_verification: Disable SSL certificate verification
            flight_port: Arrow Flight port (auto-detected based on mode if not provided)
            flight_endpoint: Arrow Flight endpoint (defaults to hostname if not provided)
            mode: Connection mode - 'cloud' (default), 'v26', or 'v25'
                  - 'cloud': Dremio Cloud (default)
                  - 'v26': Dremio Software v26+ with PAT support
                  - 'v25': Dremio Software v25 and earlier
            profile: Name of profile to use from ~/.dremio/profiles.yaml
        """
        
        from .profile import get_profile_config, get_default_profile__name
        
        # Profile Logic
        # 1. Determine profile name (arg > default > None)
        target_profile = profile or get_default_profile__name()
        
        # 2. Load profile config if we have a target profile
        profile_config = {}
        if target_profile:
             profile_config = get_profile_config(target_profile) or {}
             if not profile_config and profile:
                 print(f"Warning: Profile '{profile}' specified but not found in profiles.yaml")

        # 3. resolve arguments (Arg > Profile > Env/Default)
        
        # Type/Mode map
        # Profile uses 'type': 'cloud'/'software'
        # Client uses 'mode': 'cloud'/'v26'/'v25'
        # If profile says 'software', we default to 'v26' unless specified otherwise?
        # Actually client defaults 'cloud'.
        
        profile_type = profile_config.get("type", "").lower()
        if profile_type:
            if profile_type == "cloud":
                mode = mode if mode != "cloud" else "cloud" # Keep arg if specific, else profile
            elif profile_type == "software":
                # If user didn't override mode default 'cloud', switch to 'v26' as generic software default
                if mode == "cloud":
                     mode = "v26" 
        
        self.mode = mode.lower()
        
        # Base URL
        # Profile might have base_url
        if not base_url and profile_config.get("base_url"):
            base_url = profile_config.get("base_url")

        # Auth
        auth_config = profile_config.get("auth", {})
        profile_pat = None
        profile_username = None
        profile_password = None
        
        if auth_config.get("type") == "pat":
            profile_pat = auth_config.get("token")
        elif auth_config.get("type") == "username_password":
            profile_username = auth_config.get("username")
            profile_password = auth_config.get("password")
            
        # SSL
        # Profile has ssl: 'true'/'false' (string or bool)
        profile_tls = None
        if "ssl" in profile_config:
            val = profile_config["ssl"]
            if isinstance(val, str):
                profile_tls = val.lower() == "true"
            else:
                profile_tls = bool(val)

        # Apply Priority
        # PAT
        self.pat = pat or profile_pat
        
        # Project ID
        self.project_id = project_id or profile_config.get("project_id")
        
        # Hostname - extract from base_url if needed later, but here we prioritize arg
        # If hostname arg is default "data.dremio.cloud" AND we have a base_url in profile,
        # we might want to derive hostname from base_url if we are in software mode.
        
        if hostname == "data.dremio.cloud" and base_url:
             # Try to extract hostname from base_url
             # https://dremio.org/api/v3 -> dremio.org
             try:
                 from urllib.parse import urlparse
                 parsed = urlparse(base_url)
                 hostname = parsed.hostname or hostname
             except:
                 pass

        # Username/Password
        self._username = username or profile_username
        self.password = password or profile_password
        
        # TLS
        if tls is True and profile_tls is not None:
             # Arg default is True, so if profile is False, we should probably respect profile?
             # But we can't distinguish explicit True vs default True easily.
             # Let's assume if profile specifies it, we use it, unless user explicitly passed tls=False?
             # For now, let's say Profile overrides default, but Arg overrides Profile. 
             # Since default is True, we can't know if user passed True. 
             # Let's just use profile if set, else TLS.
             self.tls = profile_tls
        else:
             self.tls = tls

        
        # Service User / OAuth Credentials
        self.client_id = client_id or os.getenv("DREMIO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("DREMIO_CLIENT_SECRET")
        self.token_expires_at = 0  # Timestamp when token expires
        
        # Get credentials based on mode
        # Mode determines which environment variables to prioritize
        if self.mode == "cloud":
            # Cloud mode: use DREMIO_PAT and DREMIO_PROJECT_ID
            self.pat = self.pat or os.getenv("DREMIO_PAT")
            self.project_id = self.project_id or os.getenv("DREMIO_PROJECT_ID")
            
            # Check for OAuth credentials if PAT is missing
            self.client_id = self.client_id or os.getenv("DREMIO_CLIENT_ID")
            self.client_secret = self.client_secret or os.getenv("DREMIO_CLIENT_SECRET")
        elif self.mode in ["v26", "v25"]:
            # Software mode: use DREMIO_SOFTWARE_* variables
            self.pat = self.pat or os.getenv("DREMIO_SOFTWARE_PAT")
            self.project_id = None  # Explicitly None for Software
            # Override hostname from env if not provided
            if hostname == "data.dremio.cloud":  # Default wasn't changed
                env_host = os.getenv("DREMIO_SOFTWARE_HOST")
                if env_host:
                    # Extract hostname from URL if needed
                    hostname = env_host.replace("https://", "").replace("http://", "")
                    if ":" in hostname:
                        hostname = hostname.split(":")[0]
            
            # Check for OAuth credentials if PAT is missing
            self.client_id = self.client_id or os.getenv("DREMIO_CLIENT_ID")
            self.client_secret = self.client_secret or os.getenv("DREMIO_CLIENT_SECRET")
        else:
            raise ValueError(f"Invalid mode: {self.mode}. Must be 'cloud', 'v26', or 'v25'")
        
        # Connection details
        # Sanitize hostname if it contains protocol
        if hostname and (hostname.startswith("http://") or hostname.startswith("https://")):
             hostname = hostname.replace("https://", "").replace("http://", "")
        
        self.hostname = hostname
        # self._username = username  <-- Redundant/Destructive
        # self.password = password   <-- Redundant/Destructive
        self.tls = tls
        self.disable_certificate_verification = disable_certificate_verification
        
        # Set smart defaults based on mode
        if self.mode == "cloud":
            self.port = port if port is not None else 443
            self.flight_port = flight_port if flight_port is not None else 443
            self.flight_endpoint = flight_endpoint or "data.dremio.cloud"
            if not base_url:
                self.base_url = "https://api.dremio.cloud/v0"
            else:
                self.base_url = base_url
                
        elif self.mode == "v26":
            # Dremio Software v26+ with PAT support
            # REST API typically on port 443 or 9047
            # Flight typically on port 32010
            self.port = port if port is not None else (443 if tls else 9047)
            self.flight_port = flight_port if flight_port is not None else 32010
            self.flight_endpoint = flight_endpoint or hostname
            if not base_url:
                protocol = "https" if tls else "http"
                self.base_url = f"{protocol}://{hostname}:{self.port}/api/v3"
            else:
                self.base_url = base_url
                
        elif self.mode == "v25":
            # Dremio Software v25 and earlier
            # REST API on port 9047, Flight on port 32010
            self.port = port if port is not None else 9047
            self.flight_port = flight_port if flight_port is not None else 32010
            self.flight_endpoint = flight_endpoint or hostname
            if not base_url:
                protocol = "https" if tls else "http"
                self.base_url = f"{protocol}://{hostname}:9047/api/v3"
            else:
                self.base_url = base_url
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'cloud', 'v26', or 'v25'")
            
        self.session = requests.Session()

        # Validation
        if self.client_id and self.client_secret and not self.pat:
            # OAuth mode
            self.pat = None 
            self._login_oauth()
        
        # Check for 'oauth' auth type from profile (only if explicit pat/user/pass not provided)
        elif profile_config.get("auth", {}).get("type") == "oauth" and not self.pat:
             # Extract client_id/secret from auth config if not already set
             auth = profile_config.get("auth", {})
             self.client_id = self.client_id or auth.get("client_id")
             self.client_secret = self.client_secret or auth.get("client_secret")
             if self.client_id and self.client_secret:
                 self._login_oauth()
             else:
                 raise ValueError("OAuth profile requires client_id and client_secret.")

        elif not self.pat and not (self.username and self.password):
            raise ValueError("Either PAT, Username/Password, or Client ID/Secret is required.")
        
        if self.pat:
            # For Dremio Cloud, try to exchange PAT for OAuth token if not already an OAuth token
            # (Simple heuristic: PATs are usually shorter 4-5 chars? No, they are base64 strings.
            #  OAuth tokens are JWTs usually (long). 
            #  But we can just try exchange and fallback.)
            if self.mode == "cloud":
                try:
                    # Only exchange if we suspect it's a PAT (not already a JWT Bearer from _login_oauth)
                    # _login_oauth sets self.pat to the access_token.
                    # We can set a flag or just try exchange. 
                    # If it fails, we fall back to using it as is.
                    token = self._exchange_pat_for_oauth(self.pat)
                    # If successful, allow using it as Bearer
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                except Exception:
                    # Fallback to using PAT directly
                    self.session.headers.update({"Authorization": f"Bearer {self.pat}"})
            else:
                self.session.headers.update({"Authorization": f"Bearer {self.pat}"})
        elif self.username and self.password:
            # For REST API, we need to login to get a token.
            # Dremio Software /apiv3/login (v26+) or /apiv2/login (v25)
            try:
                # Determine base root (remove /api/v3 if present)
                if self.base_url.endswith("/api/v3"):
                    base_root = self.base_url[:-7] # remove /api/v3
                else:
                    base_root = self.base_url

                # Endpoints to try based on mode
                if self.mode == "v26":
                    login_endpoints = [
                        f"{self.base_url}/login",       # Standard v3
                        f"{base_root}/apiv3/login"      # v26+ alternative
                    ]
                else:  # v25
                    login_endpoints = [
                        f"{base_root}/apiv2/login",     # v25
                        f"{self.base_url}/login"        # Fallback
                    ]

                token = None
                for login_url in login_endpoints:
                    try:
                        payload = {"userName": self.username, "password": self.password}
                        headers = {"Content-Type": "application/json", "Accept": "application/json"}
                        response = requests.post(login_url, json=payload, headers=headers, verify=not self.disable_certificate_verification)
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                token = data.get("token")
                                if token:
                                    self.session.headers.update({"Authorization": f"_dremio{token}"})
                                    # Also set self.pat so Flight client can use it as Bearer token
                                    self.pat = token
                                    break # Success
                            except Exception:
                                pass
                    except Exception:
                        pass
                
                if not token:
                    print("Warning: All REST API login attempts failed.")

            except Exception as e:
                print(f"Warning: REST API login process failed: {e}")
            
        self.session.headers.update({
            "Content-Type": "application/json"
        })

        # Lazy-loaded properties
        self._catalog = None
        self._admin = None
        self._udf = None
        self._iceberg = None
        
        # Flight session cookies for maintaining project_id context
        self.flight_cookies = {}
        
        # If mode is v26 and we have PAT but no username, we might need to discover it for Flight
        if self.mode == "v26" and self.pat and not self.username:
            # We don't block here, but we'll fetch it when accessed if still None
            pass

    def _exchange_pat_for_oauth(self, pat: str) -> str:
        """
        Exchange a Personal Access Token (PAT) for a short-lived OAuth access token.
        This is the preferred authentication method for Dremio Cloud.
        """
        # Determine OAuth endpoint
        # For Cloud, currently global
        token_url = "https://api.dremio.cloud/oauth/token"
        
        if self.mode != "cloud" and self.base_url:
            # Attempt to derive for Software if supported
            token_url = f"{self.base_url}/oauth/token"

        headers = {"Content-Type": "application/json"}
        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": pat,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
        }
        
        try:
            response = requests.post(token_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("access_token")
        except Exception:
            # Raise to trigger fallback in __init__
            raise

    def _login_oauth(self):
        """
        Exchange Client ID and Secret for an OAuth token (Client Credentials Flow).
        Supported primarily for Dremio Cloud.
        """
        import time
        
        # For Cloud, the token endpoint is typically global: /oauth/token
        # For Software, it might be /apiv3/oauth/token or similar? 
        # Checking KIs: "Cloud: POST /oauth/token (Global)"
        
        token_url = "https://api.dremio.cloud/oauth/token"
        if self.mode != "cloud" and self.base_url:
            # Try to guess software oauth endpoint if supported (Dremio 24+)
            # Usually {base}/oauth/token
             token_url = f"{self.base_url}/oauth/token"

        payload = {
            "grant_type": "client_credentials"
        }
        
        # Auth can be Basic (id:secret) or in body. 
        # trying Basic Auth as it's standard.
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            response = requests.post(token_url, data=payload, auth=auth)
            
            # If Basic fails, try body?
            if response.status_code != 200:
                # Try sending credentials in body
                payload["client_id"] = self.client_id
                payload["client_secret"] = self.client_secret
                response = requests.post(token_url, data=payload)
                
            response.raise_for_status()
            data = response.json()
            
            self.pat = data.get("access_token") # Use as PAT
            self.session.headers.update({"Authorization": f"Bearer {self.pat}"})
            
            # Simple expiry management
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in - 60 # Buffer
            
        except Exception as e:
            # If OAuth fails, we can't proceed
            raise ConnectionError(f"OAuth login failed: {e}")

        # Lazy-loaded properties
        self._catalog = None
        self._admin = None
        self._udf = None
        self._iceberg = None
        
        # Flight session cookies for maintaining project_id context
        self.flight_cookies = {}
        
        # If mode is v26 and we have PAT but no username, we might need to discover it for Flight
        if self.mode == "v26" and self.pat and not self.username:
            # We don't block here, but we'll fetch it when accessed if still None
            pass

    @property
    def username(self):
        if self._username:
            return self._username
        
        # Try to discover username if not set (only for v26/Software modes where it's needed)
        if self.mode in ["v26", "v25"] and self.pat:
            try:
                self._username = self._discover_username()
            except Exception:
                pass # Return None if discovery fails
        
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    def _discover_username(self):
        """
        Attempt to discover the username from the catalog.
        Useful for v26+ where we might only have a PAT.
        """
        try:
            # We need to use the internal _catalog property or create a temporary one
            # to avoid circular dependency if Catalog needs client.username (it shouldn't)
            # But client.catalog property initializes Catalog(self)
            
            # Simple REST call to list catalog
            response = self.session.get(f"{self.base_url}/catalog")
            if response.status_code == 200:
                data = response.json()
                # data is { "data": [ ... ] }
                items = data.get("data", [])
                for item in items:
                    path = item.get("path", [])
                    if path and path[0].startswith("@"):
                        return path[0][1:] # Remove @ prefix
            return None
        except Exception:
            return None

    @property
    def catalog(self):
        if self._catalog is None:
            self._catalog = Catalog(self)
        return self._catalog

    @property
    def admin(self):
        if self._admin is None:
            self._admin = Admin(self)
        return self._admin

    @property
    def udf(self):
        if self._udf is None:
            self._udf = UDFManager(self)
        return self._udf

    @property
    def iceberg(self):
        if self._iceberg is None:
            from .iceberg import DremioIcebergClient
            self._iceberg = DremioIcebergClient(self)
        return self._iceberg

    def table(self, path: str) -> DremioBuilder:
        return DremioBuilder(self, path)

    def sql(self, query: str):
        # This will return a builder initialized with a SQL query or directly execute it.
        # For now, let's return a builder that can execute raw SQL.
        return DremioBuilder(self, sql=query)

    def execute(self, query: str, format: str = "pandas"):
        """Execute raw SQL query directly via Flight"""
        # Create a temporary builder just to access _execute_flight
        # Or better, move _execute_flight to client or utils?
        # For now, just use a builder
        return DremioBuilder(self)._execute_flight(query, format)

    def query(self, sql: str, format: str = "pandas"):
        """
        Execute a raw SQL query and return the result.
        
        Args:
            sql: The SQL query to execute.
            format: The return format ('pandas', 'arrow', 'polars').
        
        Returns:
            DataFrame or Table in the requested format.
        """
        return DremioBuilder(self, sql=sql).collect(format)

    def ingest_api(self, url: str, table_name: str, headers: dict = None, json_path: str = None, 
                   mode: str = 'append', pk: str = None, batch_size: int = None):
        """
        Ingest data from an API endpoint into Dremio.
        
        Args:
            url: The API URL.
            table_name: The target table name.
            headers: Optional headers for the request.
            json_path: Optional key to extract list of records from JSON response (e.g. "data.items").
            mode: 'replace', 'append', or 'merge'.
            pk: Primary key column for 'append' (incremental) or 'merge'.
            batch_size: Batch size for insertion.
        """
        import pandas as pd
        
        # 1. Fetch Data
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 2. Parse Data
        if json_path:
            keys = json_path.split('.')
            for k in keys:
                data = data.get(k, [])
        
        if not isinstance(data, list):
            raise ValueError("API response (or extracted path) must be a list of records")
            
        df = pd.DataFrame(data)
        if df.empty:
            print("No data fetched from API.")
            return
            
        # 3. Handle Modes
        if mode == 'replace':
            # Drop table if exists
            try:
                # We need a drop table command.
                self.execute(f"DROP TABLE IF EXISTS {table_name}")
            except Exception:
                pass # Ignore if table doesn't exist
            # Create/Insert
            # Use create with data
            try:
                self.table(table_name).create(table_name, data=df, batch_size=batch_size)
            except Exception as e:
                # If create fails (e.g. table exists but delete failed?), try insert
                # But we tried to delete rows/drop table.
                raise e
            
        elif mode == 'append':
            if pk:
                # Get max PK
                try:
                    max_val_df = self.table(table_name).agg(m=f"MAX({pk})").collect()
                    max_val = max_val_df['m'][0]
                    if max_val is not None:
                        df = df[df[pk] > max_val]
                except Exception:
                    # Table might not exist or empty
                    pass
            
            if df.empty:
                print("No new records to append.")
                return
            
            # Insert
            # If table doesn't exist, insert might fail.
            # We should check existence or just try create if insert fails?
            # For now, assume table exists for append mode, or user should use replace first.
            # But if we want to be robust:
            try:
                self.table(table_name).insert(table_name, data=df, batch_size=batch_size)
            except Exception:
                # Try create if insert failed (maybe table doesn't exist)
                self.table(table_name).create(table_name, data=df, batch_size=batch_size)

        elif mode == 'merge':
            if not pk:
                raise ValueError("Merge mode requires a primary key (pk)")
            
            # 1. Create Staging Table
            staging_table = f"{table_name}_staging_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create staging table with data
            self.table(staging_table).create(staging_table, data=df, batch_size=batch_size)
            
            # 2. Merge
            # Check if target exists. If not, just rename staging to target?
            # Or just create target from staging.
            # Assuming target exists for merge.
            
            try:
                self.table(table_name).merge(
                    target_table=table_name,
                    on=pk,
                    matched_update={col: f"source.{col}" for col in df.columns if col != pk},
                    not_matched_insert={col: f"source.{col}" for col in df.columns},
                    data=None # We are using staging table as source
                )
                # Wait, merge takes `data` or uses `self` (builder).
                # We need to create a builder for the staging table.
                self.table(staging_table).merge(
                    target_table=table_name,
                    on=pk,
                    matched_update={col: f"source.{col}" for col in df.columns if col != pk},
                    not_matched_insert={col: f"source.{col}" for col in df.columns}
                )
            except Exception as e:
                # If target doesn't exist, maybe we should have just created it?
                # But merge implies existing data.
                # If target missing, we can just CTAS from staging.
                # Check if error is "Table not found"
                if "not found" in str(e).lower():
                     self.table(staging_table).create(table_name)
                else:
                    raise e
            finally:
                # 3. Drop Staging
                self.execute(f"DROP TABLE IF EXISTS {staging_table}")

    def list_files(self, path: str) -> DremioBuilder:
        """
        Query the LIST_FILES table function for a given path.
        Useful for accessing unstructured data.
        """
        return DremioBuilder(self, f"TABLE(LIST_FILES('{path}'))")

    def upload_file(self, file_path: str, table_name: str, file_format: str = None, **kwargs):
        """
        Upload a local file to Dremio as a new table.
        
        Args:
            file_path: Path to the local file.
            table_name: Destination table name (e.g., "space.folder.table").
            file_format: 'csv', 'json', 'parquet', 'excel', 'html', 'avro', 'orc', 'lance', 'feather'. 
                         If None, inferred from extension.
            **kwargs: Additional arguments passed to the file reader.
        """
        import pyarrow as pa
        import pyarrow.csv as csv
        import pyarrow.json as json
        import pyarrow.parquet as parquet
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_format is None:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.csv':
                file_format = 'csv'
            elif ext == '.json':
                file_format = 'json'
            elif ext == '.parquet':
                file_format = 'parquet'
            elif ext in ['.xlsx', '.xls', '.ods']:
                file_format = 'excel'
            elif ext == '.html':
                file_format = 'html'
            elif ext == '.avro':
                file_format = 'avro'
            elif ext == '.orc':
                file_format = 'orc'
            elif ext == '.lance':
                file_format = 'lance'
            elif ext in ['.feather', '.arrow']:
                file_format = 'feather'
            else:
                raise ValueError(f"Could not infer format from extension {ext}. Please specify file_format.")

        table = None

        if file_format == 'csv':
            table = csv.read_csv(file_path, **kwargs)
        elif file_format == 'json':
            table = json.read_json(file_path, **kwargs)
        elif file_format == 'parquet':
            table = parquet.read_table(file_path, **kwargs)
        elif file_format == 'excel':
            try:
                import pandas as pd
                df = pd.read_excel(file_path, **kwargs)
                table = pa.Table.from_pandas(df)
            except ImportError:
                raise ImportError("pandas and openpyxl are required for Excel files. Install with `pip install pandas openpyxl`.")
        elif file_format == 'html':
            try:
                import pandas as pd
                # read_html returns a list of DataFrames
                dfs = pd.read_html(file_path, **kwargs)
                if not dfs:
                    raise ValueError("No tables found in HTML file.")
                # Default to the first table, or user can pass 'match' in kwargs to filter
                table = pa.Table.from_pandas(dfs[0])
            except ImportError:
                raise ImportError("pandas and lxml/html5lib are required for HTML files. Install with `pip install pandas lxml`.")
        elif file_format == 'avro':
            try:
                import fastavro
                with open(file_path, 'rb') as f:
                    reader = fastavro.reader(f)
                    records = list(reader)
                    table = pa.Table.from_pylist(records)
            except ImportError:
                raise ImportError("fastavro is required for Avro files. Install with `pip install fastavro`.")
        elif file_format == 'orc':
            try:
                import pyarrow.orc as orc
                table = orc.read_table(file_path, **kwargs)
            except ImportError:
                raise ImportError("pyarrow.orc is required for ORC files.")
        elif file_format == 'lance':
            try:
                import lance
                ds = lance.dataset(file_path)
                table = ds.to_table(**kwargs)
            except ImportError:
                raise ImportError("lance is required for Lance files. Install with `pip install pylance`.")
        elif file_format == 'feather':
            try:
                import pyarrow.feather as feather
                table = feather.read_table(file_path, **kwargs)
            except ImportError:
                raise ImportError("pyarrow is required for Feather files.")
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        # Create table and insert data
        self.table(table_name).create(table_name, data=table)
        print(f"Successfully uploaded {file_path} to {table_name}")

    def create_table(self, table_name: str, schema: Union[Dict[str, str], Any] = None, 
                     data: Any = None, insert_data: bool = True):
        """
        Create a new table in Dremio.
        
        Args:
            table_name: The name of the table to create (e.g., "space.folder.table").
            schema: Either:
                    - Dict mapping column names to SQL types (e.g., {"id": "INTEGER", "name": "VARCHAR"})
                    - pandas DataFrame, polars DataFrame, or pyarrow Table (schema will be inferred)
            data: Optional data to insert after table creation. Only used if schema is a dict.
                  If schema is a DataFrame/Table, it will be used for both schema and data.
            insert_data: If True and data is provided, insert the data after creating the table.
        
        Returns:
            Result of the CREATE TABLE operation.
            
        Examples:
            # Create empty table with explicit schema
            client.create_table("my_space.my_table", {
                "id": "INTEGER",
                "name": "VARCHAR",
                "created_at": "TIMESTAMP"
            })
            
            # Create table from DataFrame (infers schema and optionally inserts data)
            df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
            client.create_table("my_space.my_table", schema=df, insert_data=True)
            
            # Create empty table from DataFrame schema only
            client.create_table("my_space.my_table", schema=df, insert_data=False)
        """
        import pyarrow as pa
        import pandas as pd
        
        # Case 1: Schema is a dict - create table with explicit column definitions
        if isinstance(schema, dict):
            if not schema:
                raise ValueError("Schema dictionary cannot be empty")
            
            # Build CREATE TABLE statement
            cols_def = ", ".join([f'"{col}" {dtype}' for col, dtype in schema.items()])
            quoted_name = self._quote_table_name(table_name)
            create_sql = f"CREATE TABLE {quoted_name} ({cols_def})"
            
            # Execute CREATE TABLE
            result = self.execute(create_sql, format="polars")
            print(f"Created table {table_name}")
            
            # Optionally insert data
            if data is not None and insert_data:
                self.table(table_name).insert(table_name, data=data)
                print(f"Inserted data into {table_name}")
            
            return result
        
        # Case 2: Schema is a DataFrame or Arrow Table - infer schema
        elif schema is not None:
            # Convert to Arrow Table for consistent handling
            arrow_table = None
            
            if isinstance(schema, pd.DataFrame):
                arrow_table = pa.Table.from_pandas(schema)
            elif isinstance(schema, pa.Table):
                arrow_table = schema
            else:
                # Try polars DataFrame
                try:
                    import polars as pl
                    if isinstance(schema, pl.DataFrame):
                        arrow_table = schema.to_arrow()
                except ImportError:
                    pass
            
            if arrow_table is None:
                raise ValueError(
                    "Schema must be a dict, pandas DataFrame, polars DataFrame, or pyarrow Table"
                )
            
            # Infer SQL types from Arrow schema
            type_mapping = {
                'int8': 'INTEGER',  # Dremio doesn't support TINYINT
                'int16': 'INTEGER',  # Use INTEGER instead of SMALLINT for compatibility
                'int32': 'INTEGER',
                'int64': 'BIGINT',
                'uint8': 'INTEGER',  # Dremio doesn't support TINYINT
                'uint16': 'INTEGER',  # Use INTEGER instead of SMALLINT for compatibility
                'uint32': 'INTEGER',
                'uint64': 'BIGINT',
                'float': 'FLOAT',
                'double': 'DOUBLE',
                'bool': 'BOOLEAN',
                'string': 'VARCHAR',
                'large_string': 'VARCHAR',
                'binary': 'VARBINARY',
                'large_binary': 'VARBINARY',
                'date32': 'DATE',
                'date64': 'DATE',
                'timestamp': 'TIMESTAMP',
                'time32': 'TIME',
                'time64': 'TIME',
                'decimal128': 'DECIMAL',
                'decimal256': 'DECIMAL',
            }
            
            # Build column definitions from Arrow schema
            cols_def_list = []
            for field in arrow_table.schema:
                arrow_type = str(field.type)
                # Extract base type (e.g., "timestamp[us]" -> "timestamp")
                base_type = arrow_type.split('[')[0].split('(')[0]
                
                sql_type = type_mapping.get(base_type, 'VARCHAR')
                cols_def_list.append(f'"{field.name}" {sql_type}')
            
            cols_def = ", ".join(cols_def_list)
            quoted_name = self._quote_table_name(table_name)
            create_sql = f"CREATE TABLE {quoted_name} ({cols_def})"
            
            # Execute CREATE TABLE
            result = self.execute(create_sql, format="polars")
            print(f"Created table {table_name} with {len(arrow_table.schema)} columns")
            
            # Optionally insert data
            if insert_data and len(arrow_table) > 0:
                self.table(table_name).insert(table_name, data=arrow_table)
                print(f"Inserted {len(arrow_table)} rows into {table_name}")
            
            return result
        
        else:
            raise ValueError("Either schema dict or schema DataFrame/Table must be provided")
    
    def _quote_table_name(self, table_name: str) -> str:
        """
        Quote a table name for SQL (e.g., space.folder.table -> "space"."folder"."table").
        """
        if '"' in table_name:
            return table_name  # Assume already quoted
        parts = table_name.split(".")
        quoted_parts = [f'"{p}"' for p in parts]
        return ".".join(quoted_parts)

    @property
    def ingest(self):
        """
        Access ingestion modules.
        Example: client.ingest.dlt(source, "table")
        """
        from dremioframe import ingest
        
        class IngestNamespace:
            def __init__(self, client):
                self.client = client
                
            def dlt(self, source, table_name, **kwargs):
                return ingest.ingest_dlt(self.client, source, table_name, **kwargs)

            def database(self, connection_string, query, table_name, **kwargs):
                return ingest.ingest_database(self.client, connection_string, query, table_name, **kwargs)

            def files(self, pattern, table_name, **kwargs):
                return ingest.ingest_files(self.client, pattern, table_name, **kwargs)
                
        return IngestNamespace(self)

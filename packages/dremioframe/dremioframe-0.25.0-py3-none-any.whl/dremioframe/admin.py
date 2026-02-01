from typing import Optional, List, Any

class Admin:
    def __init__(self, client):
        self.client = client

    def _build_url(self, endpoint: str):
        """Build URL with project_id for Cloud or without for Software."""
        if self.client.project_id:
            return f"{self.client.base_url}/projects/{self.client.project_id}/{endpoint}"
        else:
            return f"{self.client.base_url}/{endpoint}"

    def _build_global_url(self, endpoint: str):
        """Build URL without project_id (for User/Admin APIs)."""
        return f"{self.client.base_url}/{endpoint}"


    # --- Users ---
    # --- Users ---
    def create_user(self, username: str, password: Optional[str] = None, 
                   first_name: str = None, last_name: str = None, 
                   email: str = None, identity_type: str = "LOCAL"):
        """
        Create a new user.
        
        Args:
            username: The unique username.
            password: Password (required for LOCAL users, optional for SERVICE_USER).
            first_name: User's first name.
            last_name: User's last name.
            email: User's email address.
            identity_type: "LOCAL" or "SERVICE_USER".
        """
        # For SERVICE_USER, we must use the REST API as SQL support is limited/varying
        if identity_type == "SERVICE_USER":
            if self.client.mode == "v25":
                 raise NotImplementedError("Service Users are not supported in Dremio Software v25")
            
            payload = {
                "name": username,
                "firstName": first_name or "Service",
                "lastName": last_name or "User",
                "email": email or f"{username}@dremio.local",
                "identityType": "SERVICE_USER"
            }
            # POST /api/v3/user (Software) or /v0/user (Cloud - separate endpoint?)
            # Both use /user endpoint in their respective base URL
            # For Cloud, this is a global endpoint (/v0/user), so we must NOT include project ID.
            if self.client.mode == "cloud":
                 url = self._build_global_url("user")
            else:
                 url = self._build_url("user")

            response = self.client.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
            
        # For LOCAL Users, we can use SQL or REST. SQL is simpler for basic user/pass
        sql = f"CREATE USER '{username}'"
        if password:
            sql += f" PASSWORD '{password}'"
        return self.client.execute(sql)

    def get_user(self, name_or_id: str):
        """
        Get a user by ID or Username (by partial match/lookup).
        """
        try:
            # Try as ID first
            if self.client.mode == "cloud":
                 url = self._build_global_url(f"user/{name_or_id}")
            else:
                 url = self._build_url(f"user/{name_or_id}")

            response = self.client.session.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
            
        # Try to find by name via internal API or just fail for now if no search endpoint
        # There isn't a clean "search user by name" in public API except maybe lookup?
        # We'll rely on ID or exact name lookups if supported.
        # Fallback: Unfortunately Dremio doesn't have a clean "get user by name" in public v3.
        # Users might need to pass the ID.
        raise ValueError(f"Could not find user with ID {name_or_id}. Note: Retrieving by username is restricted in some API versions.")

    def alter_user_password(self, username: str, password: str):
        """Change a user's password."""
        return self.client.execute(f"ALTER USER '{username}' SET PASSWORD '{password}'")

    def drop_user(self, username: str):
        """
        Delete a user.
        Note: For Service Users, it's safer to use the REST API with ID if possible, 
        but SQL DROP USER usually works by name for both if they are in the namespace.
        """
        return self.client.execute(f"DROP USER '{username}'")


    # --- Grants ---
    def grant(self, privilege: str, on: str, to_user: str = None, to_role: str = None):
        """
        Grant privileges.
        Example: grant("SELECT", "TABLE my_table", to_role="DATA_SCIENTIST")
        """
        if to_user:
            grantee = f"USER '{to_user}'"
        elif to_role:
            grantee = f"ROLE '{to_role}'"
        else:
            raise ValueError("Must specify to_user or to_role")
            
        return self.client.execute(f"GRANT {privilege} ON {on} TO {grantee}")

    def revoke(self, privilege: str, on: str, from_user: str = None, from_role: str = None):
        """
        Revoke privileges.
        """
        if from_user:
            grantee = f"USER '{from_user}'"
        elif from_role:
            grantee = f"ROLE '{from_role}'"
        else:
            raise ValueError("Must specify from_user or from_role")
            
        return self.client.execute(f"REVOKE {privilege} ON {on} FROM {grantee}")

    # --- Policies ---
    def create_policy_function(self, name: str, args: str, return_type: str, body: str):
        """
        Create a UDF to be used as a policy.
        Example: create_policy_function("mask_ssn", "ssn VARCHAR", "VARCHAR", "CASE WHEN is_member('admin') THEN ssn ELSE '***' END")
        """
        return self.create_udf(name, args, return_type, body)

    def create_udf(self, name: str, args: str, return_type: str, body: str, replace: bool = False):
        """
        Create a User Defined Function.
        Delegates to client.udf.create.
        
        Args:
            name: Name of the function.
            args: Arguments definition string (e.g., "x INT, y INT").
            return_type: Return type string (e.g., "INT").
            body: Function body SQL (e.g., "SELECT x + y").
            replace: Whether to replace if exists.
        """
        return self.client.udf.create(name, args, return_type, body, replace)

    def drop_udf(self, name: str, if_exists: bool = False):
        """
        Drop a User Defined Function.
        Delegates to client.udf.drop.
        """
        return self.client.udf.drop(name, if_exists)

    def apply_masking_policy(self, table: str, column: str, policy: str):
        """
        Apply a column masking policy.
        policy: Function name and args, e.g. "mask_ssn(ssn)"
        """
        return self.client.execute(f"ALTER TABLE {table} MODIFY COLUMN {column} SET MASKING POLICY {policy}")

    def drop_masking_policy(self, table: str, column: str, policy: str = None):
        """
        Remove a masking policy from a column.
        
        Args:
            table: Table name.
            column: Column name.
            policy: Optional policy name to unset (syntax: UNSET MASKING POLICY policy_name).
                    If not provided, just UNSET MASKING POLICY.
        """
        policy_clause = f" {policy}" if policy else ""
        return self.client.execute(f"ALTER TABLE {table} MODIFY COLUMN {column} UNSET MASKING POLICY{policy_clause}")

    def apply_row_access_policy(self, table: str, policy: str):
        """
        Apply a row access policy.
        policy: Function name and args, e.g. "region_filter(region)"
        """
        return self.client.execute(f"ALTER TABLE {table} ADD ROW ACCESS POLICY {policy}")

    def drop_row_access_policy(self, table: str, policy: str):
        """
        Remove a row access policy.
        
        Args:
            table: Table name.
            policy: Policy name to drop (e.g. "country_filter(country)").
        """
        return self.client.execute(f"ALTER TABLE {table} DROP ROW ACCESS POLICY {policy}")

    # --- Reflections ---
    def list_reflections(self):
        """List all reflections."""
        # This requires using the REST API directly as there is no SQL command for listing reflections in this detail
        # Dremio REST API: GET /api/v3/reflection
        response = self.client.session.get(self._build_url("reflection"))
        response.raise_for_status()
        return response.json()

    def create_reflection(self, dataset_id: str, name: str, type: str, 
                          display_fields: List[str] = None, 
                          dimension_fields: List[str] = None, 
                          measure_fields: List[str] = None,
                          distribution_fields: List[str] = None,
                          partition_fields: List[str] = None,
                          sort_fields: List[str] = None):
        """
        Create a reflection.
        
        Args:
            dataset_id: The ID of the dataset.
            name: Name of the reflection.
            type: "RAW" or "AGGREGATION".
            display_fields: List of fields to display (RAW only).
            dimension_fields: List of dimension fields (AGGREGATION only).
            measure_fields: List of measure fields (AGGREGATION only).
            distribution_fields: List of fields to distribute by.
            partition_fields: List of fields to partition by.
            sort_fields: List of fields to sort by.
        """
        payload = {
            "name": name,
            "type": type.upper(),
            "datasetId": dataset_id,
            "enabled": True
        }
        
        if display_fields: payload["displayFields"] = [{"name": f} for f in display_fields]
        if dimension_fields: payload["dimensionFields"] = [{"name": f} for f in dimension_fields]
        if measure_fields: payload["measureFields"] = [{"name": f} for f in measure_fields]
        if distribution_fields: payload["distributionFields"] = [{"name": f} for f in distribution_fields]
        if partition_fields: payload["partitionFields"] = [{"name": f} for f in partition_fields]
        if sort_fields: payload["sortFields"] = [{"name": f} for f in sort_fields]

        response = self.client.session.post(self._build_url("reflection"), json=payload)
        response.raise_for_status()
        return response.json()

    def delete_reflection(self, reflection_id: str):
        """Delete a reflection by ID."""
        response = self.client.session.delete(self._build_url(f"reflection/{reflection_id}"))
        response.raise_for_status()
        return True

    def enable_reflection(self, reflection_id: str):
        """Enable a reflection."""
        # First get the reflection to get the tag (version)
        ref = self._get_reflection(reflection_id)
        ref["enabled"] = True
        return self._update_reflection(reflection_id, ref)

    def disable_reflection(self, reflection_id: str):
        """Disable a reflection."""
        ref = self._get_reflection(reflection_id)
        ref["enabled"] = False
        return self._update_reflection(reflection_id, ref)

    def _get_reflection(self, reflection_id: str):
        response = self.client.session.get(self._build_url(f"reflection/{reflection_id}"))
        response.raise_for_status()
        return response.json()

    def _update_reflection(self, reflection_id: str, payload: dict):
        response = self.client.session.put(self._build_url(f"reflection/{reflection_id}"), json=payload)
        response.raise_for_status()
        return response.json()

    # --- Sources ---
    def list_sources(self):
        """List all sources."""
        response = self.client.session.get(self._build_url("source"))
        response.raise_for_status()
        return response.json()

    def get_source(self, id_or_path: str):
        """Get a source by ID or Path."""
        # Try as ID first
        try:
            response = self.client.session.get(self._build_url(f"source/{id_or_path}"))
            response.raise_for_status()
            return response.json()
        except Exception:
            # Try as path (by listing and filtering? or catalog API?)
            # Catalog API can get by path.
            return self.client.catalog.get_entity(id_or_path)

    def create_folder(self, path: str):
        """
        Create a folder using SQL (Dremio Cloud / Iceberg Catalog).
        
        Syntax: CREATE FOLDER [IF NOT EXISTS] <folder_name>
        
        Args:
            path: The path/name of the folder.
        """
        return self.client.execute(f"CREATE FOLDER IF NOT EXISTS {path}")

    def create_space(self, name: str):
        """
        Create a Space using the REST API (Dremio Software).
        
        Args:
            name: Name of the space.
        """
        if self.client.mode == "cloud":
            raise NotImplementedError("create_space is not supported in Dremio Cloud. Use create_folder instead.")
            
        payload = {
            "entityType": "space",
            "name": name
        }
        response = self.client.session.post(self._build_url("catalog"), json=payload)
        response.raise_for_status()
        return response.json()

    def create_space_folder(self, space: str, folder: str):
        """
        Create a folder in a Space using the REST API (Dremio Software).
        
        Args:
            space: Name of the space.
            folder: Name of the folder to create.
        """
        # Path is list: [space, folder]
        payload = {
            "entityType": "folder",
            "path": [space, folder]
        }
        response = self.client.session.post(self._build_url("catalog"), json=payload)
        response.raise_for_status()
        return response.json()

    def create_source(self, name: str, type: str, config: dict, 
                      acceleration_grace_period: int = 21600000,
                      acceleration_refresh_period: int = 3600000,
                      acceleration_never_expire: bool = False,
                      acceleration_never_refresh: bool = False):
        """
        Create a new source.
        
        Args:
            name: Source name.
            type: Source type (e.g., "S3", "NAS", "POSTGRES").
            config: Configuration dictionary specific to the source type.
            acceleration_*: Refresh policy settings.
        """
        payload = {
            "name": name,
            "type": type.upper(),
            "config": config,
            "accelerationGracePeriodMs": acceleration_grace_period,
            "accelerationRefreshPeriodMs": acceleration_refresh_period,
            "accelerationNeverExpire": acceleration_never_expire,
            "accelerationNeverRefresh": acceleration_never_refresh
        }
        
        response = self.client.session.post(self._build_url("source"), json=payload)
        response.raise_for_status()
        return response.json()

    def delete_source(self, id: str):
        """Delete a source by ID."""
        response = self.client.session.delete(self._build_url(f"source/{id}"))
        response.raise_for_status()
        return True

    def create_source_s3(self, name: str, bucket_name: str, 
                         access_key: str = None, secret_key: str = None, 
                         auth_type: str = "ACCESS_KEY",
                         secure: bool = True):
        """
        Helper to create an S3 source.
        
        Args:
            name: Source name.
            bucket_name: S3 bucket name.
            access_key: AWS Access Key.
            secret_key: AWS Secret Key.
            auth_type: "ACCESS_KEY", "EC2_METADATA", "NONE".
            secure: Use HTTPS (True) or HTTP (False).
        """
        config = {
            "bucketName": bucket_name,
            "authenticationType": auth_type,
            "secure": secure
        }
        
        if auth_type == "ACCESS_KEY":
            if not access_key or not secret_key:
                raise ValueError("access_key and secret_key are required for ACCESS_KEY auth")
            config["accessKey"] = access_key
            config["accessSecret"] = secret_key
            
        return self.create_source(name, "S3", config)

    # --- Profiling ---
    def get_job_profile(self, job_id: str):
        """
        Get the profile for a job.
        
        Args:
            job_id: The job ID.
            
        Returns:
            QueryProfile object.
        """
        from dremioframe.profile import QueryProfile
        
        # Dremio API: GET /api/v3/job/{id} gives job details.
        # But full profile might be different or require specific endpoint depending on version.
        # Usually /api/v3/job/{id} contains enough info for basic profiling.
        # For detailed profile (operator tree), it might be internal or different endpoint.
        # Let's use the standard job endpoint for now.
        
        response = self.client.session.get(self._build_url(f"job/{job_id}"))
        response.raise_for_status()
        return QueryProfile(response.json())
    @property
    def credentials(self):
        """Access credential management (for Service Users)."""
        return CredentialsResource(self.client)

class CredentialsResource:
    def __init__(self, client):
        self.client = client
        self.mode = client.mode

    def _build_url(self, endpoint: str):
        if self.client.project_id:
            return f"{self.client.base_url}/projects/{self.client.project_id}/{endpoint}"
        else:
            return f"{self.client.base_url}/{endpoint}"

    def create(self, user_id: str, label: str):
        """
        Create a new OAuth secret (credential) for a user.
        
        Args:
            user_id: The UUID of the user (must be a Service User).
            label: A descriptive name for the secret.
        """
        payload = {
            "name": label,
            "credentialType": "CLIENT_SECRET",
            "clientSecretConfig": {
                "duration": 0, # 0 usually means indefinite or default
                "units": "DAYS" 
            }
        }
        # Endpoint: /api/v3/user/{id}/oauth/credentials
        # Note: This endpoint might not start with /projects/{id} in Cloud depending on RBAC.
        # Usually it is /api/v3/user/... or /v0/user/... directly.
        # The Admin._build_url might prepend project logic which is correct for Catalog but maybe not User?
        # Let's use direct URL construction to be safe if User API is global.
        
        # User API is often global or requires different root.
        # Software: /api/v3/user/...
        # Cloud: /v0/user/...
        
        # We need to reuse the logic from client or admin but be careful about project prefix.
        # In Cloud, /v0/user is correct. Admin._build_url adds project if present.
        # But User management in Cloud is at Organization level usually, unless scoped?
        # Let's try to strip project if needed, or assume the base_url is correct.
        
        # Taking a safer bet: Construct from base_url but strip /projects/... if present?
        # self.client.base_url is top level.
        
        base = self.client.base_url
        if "/projects/" in base: 
            # If base_url was modified to include project (rare/custom), strip it.
            # But normally base_url is just .../v0 or .../api/v3.
            pass
            
        url = f"{base}/user/{user_id}/oauth/credentials"
        response = self.client.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def list(self, user_id: str):
        """List credentials for a user."""
        url = f"{self.client.base_url}/user/{user_id}/oauth/credentials"
        response = self.client.session.get(url)
        response.raise_for_status()
        return response.json()

    def delete(self, user_id: str, credential_id: str):
        """Delete a credential."""
        url = f"{self.client.base_url}/user/{user_id}/oauth/credentials/{credential_id}"
        response = self.client.session.delete(url)
        response.raise_for_status()
        return True

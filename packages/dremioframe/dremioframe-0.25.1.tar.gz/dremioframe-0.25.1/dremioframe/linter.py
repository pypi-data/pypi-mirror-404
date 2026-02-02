from typing import List, Dict, Any, Optional
from dremioframe.client import DremioClient
import re

class SqlLinter:
    """
    Provides SQL validation and linting capabilities.
    """
    def __init__(self, client: Optional[DremioClient] = None):
        self.client = client

    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL by running EXPLAIN PLAN in Dremio.
        Requires a connected client.
        """
        if not self.client:
            return {"valid": False, "error": "Client not provided for validation."}

        try:
            # EXPLAIN PLAN FOR <query>
            explain_sql = f"EXPLAIN PLAN FOR {sql}"
            self.client.sql(explain_sql).collect()
            return {"valid": True, "error": None}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def lint_sql(self, sql: str) -> List[str]:
        """
        Perform static checks on SQL.
        Returns a list of warnings/suggestions.
        """
        warnings = []
        
        # Check 1: SELECT *
        if re.search(r"SELECT\s+\*", sql, re.IGNORECASE):
            warnings.append("Avoid 'SELECT *' in production queries. Specify columns explicitly.")
            
        # Check 2: Missing WHERE in DELETE/UPDATE
        if re.search(r"DELETE\s+FROM", sql, re.IGNORECASE) and not re.search(r"WHERE", sql, re.IGNORECASE):
            warnings.append("DELETE statement missing WHERE clause. This will delete all rows.")
            
        if re.search(r"UPDATE\s+", sql, re.IGNORECASE) and not re.search(r"WHERE", sql, re.IGNORECASE):
            warnings.append("UPDATE statement missing WHERE clause. This will update all rows.")
            
        # Check 3: LIMIT usage
        # This is subjective, but for interactive queries it's good.
        # if not re.search(r"LIMIT", sql, re.IGNORECASE):
        #     warnings.append("Consider adding LIMIT for large tables.")
            
        return warnings

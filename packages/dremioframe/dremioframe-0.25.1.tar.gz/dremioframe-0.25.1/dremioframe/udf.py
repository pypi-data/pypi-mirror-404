from typing import Dict, Any, List, Optional, Union

class UDFManager:
    def __init__(self, client):
        self.client = client

    def create(self, name: str, args: Union[Dict[str, str], str], returns: str, body: str, replace: bool = False):
        """
        Create a SQL UDF.
        
        Args:
            name: Name of the function (e.g., "my_space.my_func").
            args: Dictionary of argument names and types (e.g., {"x": "INT", "y": "INT"}) 
                  OR a string definition (e.g., "x INT, y INT").
            returns: Return type (e.g., "INT").
            body: SQL expression body (e.g., "x + y").
            replace: If True, use CREATE OR REPLACE.
        """
        if isinstance(args, dict):
            arg_str = ", ".join([f"{k} {v}" for k, v in args.items()])
        else:
            arg_str = args
            
        create_cmd = "CREATE OR REPLACE" if replace else "CREATE"
        
        sql = f"{create_cmd} FUNCTION {name} ({arg_str}) RETURNS {returns} RETURN {body}"
        return self.client.execute(sql)

    def drop(self, name: str, if_exists: bool = False):
        """
        Drop a SQL UDF.
        """
        exists_clause = "IF EXISTS" if if_exists else ""
        sql = f"DROP FUNCTION {exists_clause} {name}"
        return self.client.execute(sql)

    def list(self, pattern: str = None) -> List[Dict[str, Any]]:
        """
        List functions (wraps catalog listing or sys.functions if available).
        Dremio doesn't have a simple "SHOW FUNCTIONS" that lists user UDFs easily in all versions.
        We can try querying information_schema if available or just list catalog.
        For now, let's assume we list from catalog if path provided, or return empty/not implemented warning.
        Actually, `SELECT * FROM INFORMATION_SCHEMA.ROUTINES` is standard.
        """
        sql = "SELECT * FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE = 'FUNCTION'"
        if pattern:
            sql += f" AND ROUTINE_NAME LIKE '%{pattern}%'"
            
        return self.client.sql(sql).collect("pandas").to_dict(orient="records")

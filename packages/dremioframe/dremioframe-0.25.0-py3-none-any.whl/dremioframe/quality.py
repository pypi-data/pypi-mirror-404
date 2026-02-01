from typing import List, Any

class DataQuality:
    def __init__(self, builder):
        self.builder = builder

    def run_check(self, condition: str, error_msg: str):
        """
        Run a check that expects 0 rows to match the condition (meaning bad data).
        Or we can check if all rows match. 
        Let's implement it as: check if ANY row fails the expectation.
        
        So if we expect col > 0, we check count(*) where NOT (col > 0).
        If count > 0, check fails.
        """
        # We need to create a new builder from the current state to run the check
        # We can't modify the current builder's state permanently.
        # So we clone the state or just build a new query string.
        
        base_sql = self.builder._compile_sql()
        check_sql = f"SELECT COUNT(*) AS bad_rows FROM ({base_sql}) AS sub WHERE NOT ({condition})"
        
        # Execute check
        df = self.builder._execute_flight(check_sql, "polars")
        bad_rows = df[0, "bad_rows"]
        
        if bad_rows > 0:
            raise ValueError(f"Data Quality Check Failed: {error_msg}. Found {bad_rows} bad rows.")
        return True

    def expect_not_null(self, col: str):
        return self.run_check(f"{col} IS NOT NULL", f"Column {col} contains NULLs")

    def expect_unique(self, col: str):
        # Uniqueness check is harder with the simple run_check logic above.
        # We need to aggregate.
        base_sql = self.builder._compile_sql()
        check_sql = f"""
            SELECT COUNT(*) as duplicates 
            FROM (
                SELECT {col}, COUNT(*) as cnt 
                FROM ({base_sql}) AS sub 
                GROUP BY {col} 
                HAVING COUNT(*) > 1
            ) AS dupes
        """
        df = self.builder._execute_flight(check_sql, "polars")
        duplicates = df[0, "duplicates"]
        
        if duplicates > 0:
            raise ValueError(f"Data Quality Check Failed: Column {col} is not unique. Found {duplicates} duplicate values.")
        return True

    def expect_values_in(self, col: str, values: List[Any]):
        vals_str = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in values])
        return self.run_check(f"{col} IN ({vals_str})", f"Column {col} contains values not in {values}")

    def expect_row_count(self, condition: str, threshold: int, operator: str = "eq"):
        """
        Check if the number of rows matching the condition meets the threshold.
        
        Args:
            condition: SQL WHERE clause condition (e.g., "age < 0").
            threshold: The number to compare against.
            operator: Comparison operator ("eq", "ne", "gt", "lt", "ge", "le").
        """
        base_sql = self.builder._compile_sql()
        check_sql = f"SELECT COUNT(*) AS cnt FROM ({base_sql}) AS sub WHERE {condition}"
        
        df = self.builder._execute_flight(check_sql, "polars")
        count = df[0, "cnt"]
        
        ops = {
            "eq": lambda x, y: x == y,
            "ne": lambda x, y: x != y,
            "gt": lambda x, y: x > y,
            "lt": lambda x, y: x < y,
            "ge": lambda x, y: x >= y,
            "le": lambda x, y: x <= y
        }
        
        if operator not in ops:
            raise ValueError(f"Invalid operator: {operator}. Must be one of {list(ops.keys())}")
            
        if not ops[operator](count, threshold):
            raise ValueError(f"Custom Quality Check Failed: Count of rows where ({condition}) is {count}, expected {operator} {threshold}.")
        
        return True

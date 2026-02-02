import pandas as pd
from typing import List, Dict, Any

def assert_dataframes_equal(df1: pd.DataFrame, df2: pd.DataFrame, 
                            check_dtype: bool = True,
                            check_column_order: bool = False):
    """
    Assert that two DataFrames are equal.
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame
        check_dtype: Whether to check data types
        check_column_order: Whether column order must match
    
    Raises:
        AssertionError: If DataFrames are not equal
    """
    # Check shape
    if df1.shape != df2.shape:
        raise AssertionError(
            f"DataFrames have different shapes: {df1.shape} vs {df2.shape}"
        )
    
    # Check columns
    if check_column_order:
        if list(df1.columns) != list(df2.columns):
            raise AssertionError(
                f"Column order differs: {list(df1.columns)} vs {list(df2.columns)}"
            )
    else:
        if set(df1.columns) != set(df2.columns):
            raise AssertionError(
                f"Columns differ: {set(df1.columns)} vs {set(df2.columns)}"
            )
        # Reorder df2 to match df1
        df2 = df2[df1.columns]
    
    # Check dtypes
    if check_dtype:
        for col in df1.columns:
            if df1[col].dtype != df2[col].dtype:
                raise AssertionError(
                    f"Column '{col}' has different dtype: {df1[col].dtype} vs {df2[col].dtype}"
                )
    
    # Check values
    try:
        pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype)
    except AssertionError as e:
        raise AssertionError(f"DataFrame values differ: {str(e)}")

def assert_schema_matches(df: pd.DataFrame, expected_schema: Dict[str, str]):
    """
    Assert that a DataFrame matches an expected schema.
    
    Args:
        df: DataFrame to check
        expected_schema: Dictionary mapping column names to expected types
    
    Raises:
        AssertionError: If schema doesn't match
    """
    # Check all expected columns exist
    missing_cols = set(expected_schema.keys()) - set(df.columns)
    if missing_cols:
        raise AssertionError(f"Missing columns: {missing_cols}")
    
    # Check extra columns
    extra_cols = set(df.columns) - set(expected_schema.keys())
    if extra_cols:
        raise AssertionError(f"Unexpected columns: {extra_cols}")
    
    # Check types
    for col, expected_type in expected_schema.items():
        actual_type = str(df[col].dtype)
        
        # Normalize type names for comparison
        if expected_type in ['int', 'int64', 'integer']:
            if not actual_type.startswith('int'):
                raise AssertionError(
                    f"Column '{col}' has wrong type: expected int, got {actual_type}"
                )
        elif expected_type in ['float', 'float64', 'double']:
            if not actual_type.startswith('float'):
                raise AssertionError(
                    f"Column '{col}' has wrong type: expected float, got {actual_type}"
                )
        elif expected_type in ['str', 'string', 'object']:
            if actual_type != 'object':
                raise AssertionError(
                    f"Column '{col}' has wrong type: expected string, got {actual_type}"
                )
        elif expected_type != actual_type:
            raise AssertionError(
                f"Column '{col}' has wrong type: expected {expected_type}, got {actual_type}"
            )

def assert_query_valid(sql: str):
    """
    Assert that a SQL query is syntactically valid (basic check).
    
    Args:
        sql: SQL query string
    
    Raises:
        AssertionError: If query appears invalid
    """
    sql = sql.strip()
    
    # Basic checks
    if not sql:
        raise AssertionError("Query is empty")
    
    # Check for common SQL keywords
    sql_upper = sql.upper()
    valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']
    
    if not any(sql_upper.startswith(keyword) for keyword in valid_starts):
        raise AssertionError(
            f"Query doesn't start with a valid SQL keyword: {sql[:50]}"
        )
    
    # Check for balanced parentheses
    if sql.count('(') != sql.count(')'):
        raise AssertionError("Unbalanced parentheses in query")
    
    # Check for semicolon at end (optional but common)
    # This is just a warning, not an error
    if not sql.endswith(';') and not sql.endswith(')'):
        # Could add a warning here if needed
        pass

def assert_row_count(df: pd.DataFrame, expected_count: int, 
                    operator: str = 'eq'):
    """
    Assert DataFrame has expected number of rows.
    
    Args:
        df: DataFrame to check
        expected_count: Expected row count
        operator: Comparison operator ('eq', 'gt', 'lt', 'ge', 'le')
    """
    actual_count = len(df)
    
    operators = {
        'eq': lambda a, b: a == b,
        'gt': lambda a, b: a > b,
        'lt': lambda a, b: a < b,
        'ge': lambda a, b: a >= b,
        'le': lambda a, b: a <= b
    }
    
    if operator not in operators:
        raise ValueError(f"Invalid operator: {operator}")
    
    if not operators[operator](actual_count, expected_count):
        raise AssertionError(
            f"Row count assertion failed: {actual_count} {operator} {expected_count}"
        )

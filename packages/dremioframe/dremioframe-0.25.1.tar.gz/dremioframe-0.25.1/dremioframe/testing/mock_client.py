from typing import Dict, Any, Optional, Callable
import pandas as pd
from unittest.mock import MagicMock

class MockDremioClient:
    """
    Mock implementation of DremioClient for testing.
    
    Allows configuring query responses without requiring a live Dremio connection.
    """
    def __init__(self, responses: Dict[str, pd.DataFrame] = None):
        """
        Initialize mock client.
        
        Args:
            responses: Dictionary mapping SQL queries to DataFrame responses
        """
        self.responses = responses or {}
        self.query_history = []
        self.base_url = "http://mock-dremio:9047"
        self.project_id = "mock-project"
        self.headers = {"Authorization": "Bearer mock-token"}
        
        # Mock sub-objects
        self.catalog = MagicMock()
        self.admin = MagicMock()
        self.iceberg = MagicMock()
        
    def sql(self, query: str):
        """
        Execute a SQL query (mocked).
        
        Returns a MockQueryResult that can be collected.
        """
        self.query_history.append(query)
        
        # Find matching response
        response_df = None
        
        # Exact match
        if query in self.responses:
            response_df = self.responses[query]
        else:
            # Partial match (for flexibility)
            for pattern, df in self.responses.items():
                if pattern.lower() in query.lower():
                    response_df = df
                    break
        
        # Default empty response
        if response_df is None:
            response_df = pd.DataFrame()
        
        return MockQueryResult(response_df)
    
    def add_response(self, query: str, response: pd.DataFrame):
        """Add a query response mapping"""
        self.responses[query] = response
    
    def add_response_function(self, query_pattern: str, func: Callable[[str], pd.DataFrame]):
        """Add a dynamic response function"""
        self.responses[query_pattern] = func
    
    def clear_history(self):
        """Clear query history"""
        self.query_history = []
    
    def get_last_query(self) -> Optional[str]:
        """Get the last executed query"""
        return self.query_history[-1] if self.query_history else None

class MockQueryResult:
    """Mock query result that mimics DremioBuilder"""
    def __init__(self, df: pd.DataFrame):
        self._df = df
    
    def collect(self, library: str = "pandas"):
        """Return the mocked DataFrame"""
        if library == "pandas":
            return self._df
        elif library == "polars":
            try:
                import polars as pl
                return pl.from_pandas(self._df)
            except ImportError:
                raise ImportError("polars is required for library='polars'")
        else:
            raise ValueError(f"Unsupported library: {library}")
    
    def show(self, n: int = 20):
        """Print the DataFrame"""
        print(self._df.head(n))
    
    def limit(self, n: int):
        """Return a limited result"""
        return MockQueryResult(self._df.head(n))
    
    def filter(self, condition: str):
        """Return self for chaining"""
        return self
    
    def select(self, *columns):
        """Return self for chaining"""
        return self

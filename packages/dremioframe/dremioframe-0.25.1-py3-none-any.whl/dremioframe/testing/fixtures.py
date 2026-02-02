from typing import Dict, Any, List
import pandas as pd
import json
import os

class FixtureManager:
    """
    Manages test fixtures and sample data.
    """
    def __init__(self, fixtures_dir: str = None):
        """
        Initialize fixture manager.
        
        Args:
            fixtures_dir: Directory containing fixture files
        """
        self.fixtures_dir = fixtures_dir or os.path.join(os.getcwd(), 'fixtures')
        self.fixtures: Dict[str, pd.DataFrame] = {}
    
    def load_csv(self, name: str, filepath: str = None) -> pd.DataFrame:
        """
        Load a CSV fixture.
        
        Args:
            name: Fixture name
            filepath: Path to CSV file (uses fixtures_dir/name.csv if not provided)
        """
        if filepath is None:
            filepath = os.path.join(self.fixtures_dir, f"{name}.csv")
        
        df = pd.read_csv(filepath)
        self.fixtures[name] = df
        return df
    
    def load_json(self, name: str, filepath: str = None) -> pd.DataFrame:
        """
        Load a JSON fixture.
        
        Args:
            name: Fixture name
            filepath: Path to JSON file
        """
        if filepath is None:
            filepath = os.path.join(self.fixtures_dir, f"{name}.json")
        
        df = pd.read_json(filepath)
        self.fixtures[name] = df
        return df
    
    def create_fixture(self, name: str, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Create a fixture from a list of dictionaries.
        
        Args:
            name: Fixture name
            data: List of row dictionaries
        """
        df = pd.DataFrame(data)
        self.fixtures[name] = df
        return df
    
    def get(self, name: str) -> pd.DataFrame:
        """Get a loaded fixture by name"""
        if name not in self.fixtures:
            raise KeyError(f"Fixture '{name}' not found. Load it first.")
        return self.fixtures[name].copy()
    
    def save_csv(self, name: str, filepath: str = None):
        """
        Save a fixture to CSV.
        
        Args:
            name: Fixture name
            filepath: Output path
        """
        if name not in self.fixtures:
            raise KeyError(f"Fixture '{name}' not found")
        
        if filepath is None:
            os.makedirs(self.fixtures_dir, exist_ok=True)
            filepath = os.path.join(self.fixtures_dir, f"{name}.csv")
        
        self.fixtures[name].to_csv(filepath, index=False)
    
    def save_json(self, name: str, filepath: str = None):
        """Save a fixture to JSON"""
        if name not in self.fixtures:
            raise KeyError(f"Fixture '{name}' not found")
        
        if filepath is None:
            os.makedirs(self.fixtures_dir, exist_ok=True)
            filepath = os.path.join(self.fixtures_dir, f"{name}.json")
        
        self.fixtures[name].to_json(filepath, orient='records', indent=2)
    
    def list_fixtures(self) -> List[str]:
        """List all loaded fixtures"""
        return list(self.fixtures.keys())
    
    def clear(self):
        """Clear all loaded fixtures"""
        self.fixtures = {}

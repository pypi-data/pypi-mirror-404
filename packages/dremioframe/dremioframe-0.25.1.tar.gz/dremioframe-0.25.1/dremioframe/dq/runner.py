import os
import yaml
import glob
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from ..client import DremioClient
from ..quality import DataQuality

console = Console()

class DQRunner:
    def __init__(self, client: DremioClient):
        self.client = client

    def load_tests(self, directory: str) -> List[Dict[str, Any]]:
        """
        Load test definitions from YAML files in the directory.
        """
        tests = []
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")

        files = glob.glob(os.path.join(directory, "*.yaml")) + glob.glob(os.path.join(directory, "*.yml"))
        
        for f in files:
            try:
                with open(f, 'r') as stream:
                    data = yaml.safe_load(stream)
                    if isinstance(data, list):
                        tests.extend(data)
                    elif isinstance(data, dict) and "tests" in data:
                        tests.extend(data["tests"])
                    else:
                        console.print(f"[yellow]Skipping {f}: Invalid format (must be list or dict with 'tests' key)[/yellow]")
            except Exception as e:
                console.print(f"[red]Error loading {f}: {e}[/red]")
                
        return tests

    def run_tests(self, tests: List[Dict[str, Any]]) -> bool:
        """
        Run a list of tests. Returns True if all passed, False otherwise.
        """
        results = []
        all_passed = True
        
        for test in tests:
            name = test.get("name", "Unnamed Test")
            table_name = test.get("table")
            checks = test.get("checks", [])
            
            if not table_name:
                console.print(f"[red]Skipping test '{name}': Missing 'table' field[/red]")
                continue
                
            try:
                # Create builder for the table
                builder = self.client.data(table_name)
                dq = DataQuality(builder)
                
                for check in checks:
                    check_type = check.get("type")
                    column = check.get("column")
                    
                    try:
                        if check_type == "not_null":
                            dq.expect_not_null(column)
                        elif check_type == "unique":
                            dq.expect_unique(column)
                        elif check_type == "values_in":
                            values = check.get("values", [])
                            dq.expect_values_in(column, values)
                        elif check_type == "custom_sql":
                            condition = check.get("condition")
                            error_msg = check.get("error_msg", "Custom check failed")
                            dq.run_check(condition, error_msg)
                        elif check_type == "row_count":
                            condition = check.get("condition", "1=1")
                            threshold = check.get("threshold", 0)
                            operator = check.get("operator", "gt")
                            dq.expect_row_count(condition, threshold, operator)
                        else:
                            raise ValueError(f"Unknown check type: {check_type}")
                            
                        results.append({"name": name, "table": table_name, "check": check_type, "status": "PASS", "error": ""})
                    except Exception as e:
                        all_passed = False
                        results.append({"name": name, "table": table_name, "check": check_type, "status": "FAIL", "error": str(e)})
                        
            except Exception as e:
                all_passed = False
                results.append({"name": name, "table": table_name, "check": "SETUP", "status": "ERROR", "error": str(e)})

        # Print Results
        table = Table(title="Data Quality Results")
        table.add_column("Test Name")
        table.add_column("Table")
        table.add_column("Check Type")
        table.add_column("Status")
        table.add_column("Error")
        
        for r in results:
            color = "green" if r["status"] == "PASS" else "red"
            table.add_row(r["name"], r["table"], r["check"], f"[{color}]{r['status']}[/{color}]", r["error"])
            
        console.print(table)
        return all_passed

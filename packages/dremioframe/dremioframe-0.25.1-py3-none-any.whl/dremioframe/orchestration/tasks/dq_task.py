from typing import List, Dict, Any, Optional
from ..pipeline import Task
from ...client import DremioClient

class DataQualityTask(Task):
    """
    Task to run Data Quality checks.
    
    Args:
        name: Task name.
        client: DremioClient instance.
        directory: Path to directory containing YAML test files (optional).
        tests: List of test definitions (optional, if directory not provided).
    """
    def __init__(self, name: str, client: DremioClient, directory: Optional[str] = None, tests: Optional[List[Dict[str, Any]]] = None):
        # Pass a dummy action since we override run()
        super().__init__(name, lambda ctx: None)
        self.client = client
        self.directory = directory
        self.tests = tests
        
        if not self.directory and not self.tests:
            raise ValueError("DataQualityTask requires either 'directory' or 'tests'.")

    def run(self, context: Dict[str, Any]):
        try:
            from ...dq.runner import DQRunner
        except ImportError:
            raise ImportError("dremioframe[dq] is required for DataQualityTask.")
            
        runner = DQRunner(self.client)
        
        tests_to_run = []
        if self.directory:
            tests_to_run.extend(runner.load_tests(self.directory))
        if self.tests:
            tests_to_run.extend(self.tests)
            
        if not tests_to_run:
            print(f"[{self.name}] No tests to run.")
            return
            
        success = runner.run_tests(tests_to_run)
        
        if not success:
            self.status = "FAILED"
            raise RuntimeError(f"Data Quality checks failed for task '{self.name}'.")
        
        self.status = "SUCCESS"
        print(f"[{self.name}] Data Quality checks passed.")

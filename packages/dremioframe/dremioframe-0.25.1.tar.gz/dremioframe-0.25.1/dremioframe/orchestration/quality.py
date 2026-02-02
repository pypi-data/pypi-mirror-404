from typing import Callable, Any
from .task import Task

class DataQualityTask(Task):
    def __init__(self, name: str, check_function: Callable[..., bool], args: tuple = (), kwargs: dict = {}, stop_on_failure: bool = True):
        super().__init__(name, check_function, args, kwargs)
        self.stop_on_failure = stop_on_failure

    def run(self, context: dict = None):
        print(f"Running Data Quality Check: {self.name}")
        self.status = "RUNNING"
        try:
            # Expecting the check_function to return True (Pass) or False (Fail)
            # or raise an exception.
            result = self.action(*self.args, **self.kwargs)
            
            if result is True:
                self.status = "SUCCESS"
                print(f"Data Quality Check {self.name} PASSED.")
                self.result = True
            else:
                self.status = "FAILED"
                print(f"Data Quality Check {self.name} FAILED.")
                self.result = False
                if self.stop_on_failure:
                    raise Exception(f"Data Quality Check {self.name} failed.")
            
            return self.result
        except Exception as e:
            self.status = "FAILED"
            print(f"Data Quality Check {self.name} failed with error: {e}")
            raise e

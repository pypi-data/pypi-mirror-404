import abc
import concurrent.futures
from typing import List, Dict, Any, Callable
from .task import Task
from .backend import BaseBackend

try:
    from celery import Celery
except ImportError:
    Celery = None

class BaseExecutor(abc.ABC):
    """Abstract base class for task executors."""
    
    def __init__(self, backend: BaseBackend):
        self.backend = backend

    @abc.abstractmethod
    def submit_task(self, task: Task, context: dict, run_id: str):
        """Submits a task for execution."""
        pass

    @abc.abstractmethod
    def wait_for_completion(self, futures: Dict[Any, Task]) -> Dict[str, Any]:
        """Waits for submitted tasks to complete and returns results."""
        pass

class LocalExecutor(BaseExecutor):
    """Executes tasks locally using threads."""
    
    def __init__(self, backend: BaseBackend, max_workers: int = 1):
        super().__init__(backend)
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit_task(self, task: Task, context: dict, run_id: str):
        future = self.executor.submit(task.run, context=context)
        return future

    def wait_for_completion(self, futures: Dict[Any, Task]) -> Dict[str, Any]:
        # futures maps Future object -> Task
        if not futures:
            return {}
            
        done, _ = concurrent.futures.wait(
            futures.keys(), 
            return_when=concurrent.futures.FIRST_COMPLETED
        )
        
        results = {}
        for future in done:
            task = futures.pop(future)
            try:
                result = future.result()
                results[task.name] = {"status": "SUCCESS", "result": result}
            except Exception as e:
                results[task.name] = {"status": "FAILED", "error": e}
                
        return results

    def shutdown(self):
        self.executor.shutdown()

class CeleryExecutor(BaseExecutor):
    """
    Executes tasks using Celery.
    Requires `celery` and `redis` (or other broker).
    """
    def __init__(self, backend: BaseBackend, broker_url: str = "redis://localhost:6379/0"):
        super().__init__(backend)
        if Celery is None:
            raise ImportError("celery is required for CeleryExecutor. Install with `pip install dremioframe[celery]`")
            
        self.app = Celery("dremioframe_orchestration", broker=broker_url)
        self.app.conf.update(
            result_backend=broker_url,
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"]
        )

    def submit_task(self, task: Task, context: dict, run_id: str):
        # Using the generic wrapper defined below
        import pickle
        import base64
        
        # Pickle the task object
        # Note: This requires the task object and its action to be picklable.
        # Lambdas and nested functions might fail.
        try:
            pickled_task = base64.b64encode(pickle.dumps(task)).decode("utf-8")
        except AttributeError:
             raise ValueError(f"Task {task.name} cannot be pickled. Ensure action is a top-level function.")

        # Send to Celery
        # We use send_task to avoid needing the task registered in the client's app instance
        # The worker must have the task registered.
        result = self.app.send_task("dremioframe.execute_pickled_task", args=[pickled_task, context])
        return result

    def wait_for_completion(self, futures: Dict[Any, Task]) -> Dict[str, Any]:
        # futures maps AsyncResult -> Task
        import time
        
        results = {}
        # Simple polling for now
        # In a real system, we might want to use a blocking wait on the group, 
        # but we have individual results here.
        
        # We iterate and check ready()
        # If none ready, sleep briefly
        
        while not results:
            if not futures:
                break
                
            for ar in list(futures.keys()):
                if ar.ready():
                    task = futures.pop(ar)
                    try:
                        # get() might raise if task failed
                        res = ar.get()
                        results[task.name] = {"status": "SUCCESS", "result": res}
                    except Exception as e:
                        results[task.name] = {"status": "FAILED", "error": e}
            
            if results:
                break
            
            time.sleep(0.1)
            
        return results

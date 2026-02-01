from typing import Callable, Any
from .task import Task

def task(name: str = None, retries: int = 0, retry_delay: float = 1.0, trigger_rule: str = "all_success"):
    """
    Decorator to convert a function into a Task factory.
    
    Usage:
    @task(name="my_task", retries=3, trigger_rule="one_failed")
    def my_func(x, y):
        return x + y
        
    t1 = my_func(1, 2) # Returns a Task instance
    """
    def decorator(func: Callable[..., Any]):
        def wrapper(*args, **kwargs) -> Task:
            task_name = name or func.__name__
            return Task(task_name, func, args=args, kwargs=kwargs, retries=retries, retry_delay=retry_delay, trigger_rule=trigger_rule)
        return wrapper
    return decorator

import time
from typing import Callable, List, Any, Optional, Set

class Task:
    def __init__(self, name: str, action: Callable[..., Any], args: tuple = (), kwargs: dict = {}, retries: int = 0, retry_delay: float = 1.0, trigger_rule: str = "all_success"):
        self.name = name
        self.action = action
        self.args = args
        self.kwargs = kwargs
        self.retries = retries
        self.retry_delay = retry_delay
        self.trigger_rule = trigger_rule # all_success, one_failed, all_done
        self.upstream_tasks: Set['Task'] = set()
        self.downstream_tasks: Set['Task'] = set()
        self.result = None
        self.status = "PENDING" # PENDING, RUNNING, SUCCESS, FAILED, SKIPPED

    def set_upstream(self, task: 'Task'):
        self.upstream_tasks.add(task)
        task.downstream_tasks.add(self)
        return self

    def set_downstream(self, task: 'Task'):
        task.set_upstream(self)
        return task

    def on_kill(self):
        """
        Override this method to define cleanup logic when a task is killed.
        """
        pass

    def run(self, context: dict = None):
        print(f"Running task: {self.name}")
        self.status = "RUNNING"
        
        # Inject context if requested by the action
        # This is a simple heuristic: if 'context' is in kwargs, pass it.
        # A more robust way would be to inspect the signature, but let's keep it simple for now.
        # Or we can just merge context into kwargs if keys don't collide.
        run_kwargs = self.kwargs.copy()
        if context:
            # If the function explicitly asks for 'context', pass the whole dict
            # Otherwise, we could unpack context into kwargs, but that might be risky with collisions.
            # Let's stick to explicit 'context' argument for now if needed, 
            # OR allow tasks to access upstream results via a special mechanism.
            # For this implementation: we pass context as a kwarg named 'context' ONLY if the user passed it in self.kwargs as a placeholder?
            # Actually, let's just pass it if the user defined the task to accept **kwargs or specific args.
            # To be safe and simple: We will NOT automatically unpack context. 
            # We will pass the `context` object itself if the function signature allows it? 
            # No, let's rely on the user passing `context` in kwargs if they want it, and we update that ref.
            pass

        attempts = 0
        while attempts <= self.retries:
            try:
                # We pass context to the action if the action expects it? 
                # Let's assume the user handles args. 
                # BUT, for XComs, we might want to pass the context.
                # Let's try to pass 'context' as a keyword argument if the function accepts it.
                # For now, we'll just run as is.
                
                # If the user wants to use context, they should define their function to accept it,
                # and we should pass it.
                # Let's try to pass it if we can.
                try:
                    self.result = self.action(*self.args, context=context, **self.kwargs)
                except TypeError:
                    # Fallback: maybe function doesn't accept context
                    self.result = self.action(*self.args, **self.kwargs)
                
                self.status = "SUCCESS"
                print(f"Task {self.name} completed successfully.")
                return self.result
            except Exception as e:
                attempts += 1
                if attempts <= self.retries:
                    print(f"Task {self.name} failed with error: {e}. Retrying in {self.retry_delay}s... ({attempts}/{self.retries})")
                    time.sleep(self.retry_delay)
                else:
                    self.status = "FAILED"
                    print(f"Task {self.name} failed after {self.retries} retries with error: {e}")
                    raise e

    def __repr__(self):
        return f"<Task name={self.name} status={self.status}>"

from typing import List, Dict, Set, Optional, Callable, Any
from .task import Task
from .backend import BaseBackend, InMemoryBackend, PipelineRun
from .executors import BaseExecutor, LocalExecutor
import uuid
from collections import deque
import concurrent.futures
import time

class Pipeline:
    def __init__(self, name: str, max_workers: int = 1, backend: BaseBackend = None, executor: BaseExecutor = None):
        self.name = name
        self.tasks: Dict[str, Task] = {}
        self.max_workers = max_workers
        self.backend = backend or InMemoryBackend()
        self.executor = executor or LocalExecutor(self.backend, max_workers)

    def add_task(self, task: Task):
        if task.name in self.tasks:
            raise ValueError(f"Task with name {task.name} already exists in pipeline.")
        self.tasks[task.name] = task
        return self

    def _get_topological_sort(self) -> List[Task]:
        # Kahn's algorithm for topological sort
        in_degree = {task.name: 0 for task in self.tasks.values()}
        for task in self.tasks.values():
            for downstream in task.downstream_tasks:
                in_degree[downstream.name] += 1

        queue = deque([task for task in self.tasks.values() if in_degree[task.name] == 0])
        sorted_tasks = []

        while queue:
            task = queue.popleft()
            sorted_tasks.append(task)

            for downstream in task.downstream_tasks:
                in_degree[downstream.name] -= 1
                if in_degree[downstream.name] == 0:
                    queue.append(downstream)

        if len(sorted_tasks) != len(self.tasks):
            raise ValueError("Pipeline contains a cycle (circular dependency).")

        return sorted_tasks

    def run(self, context: dict = None):
        print(f"Starting pipeline: {self.name}")
        
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize run in backend
        pipeline_run = PipelineRun(
            pipeline_name=self.name,
            run_id=run_id,
            start_time=start_time,
            status="RUNNING",
            tasks={name: "PENDING" for name in self.tasks}
        )
        self.backend.save_run(pipeline_run)
        
        pipeline_context = context or {}
        task_status = {name: "PENDING" for name in self.tasks}
        
        in_degree = {task.name: 0 for task in self.tasks.values()}
        for task in self.tasks.values():
            for downstream in task.downstream_tasks:
                in_degree[downstream.name] += 1
        
        # Tasks ready to run (in-degree 0)
        ready_tasks = deque([task for task in self.tasks.values() if in_degree[task.name] == 0])
        
        # Map of Future/AsyncResult -> Task
        active_futures = {}
            
        # Helper to submit or skip
        def process_ready_task(task):
            # Evaluate trigger rule
            should_run = self._evaluate_trigger_rule(task, task_status)
            
            if should_run:
                print(f"Submitting task {task.name} (Rule: {task.trigger_rule})")
                future = self.executor.submit_task(task, pipeline_context, run_id)
                active_futures[future] = task
                task_status[task.name] = "RUNNING"
                self.backend.update_task_status(run_id, task.name, "RUNNING")
            else:
                print(f"Skipping task {task.name} (Rule: {task.trigger_rule} not met)")
                task.status = "SKIPPED"
                task_status[task.name] = "SKIPPED"
                self.backend.update_task_status(run_id, task.name, "SKIPPED")
                # If skipped, it's "done", so we process its children immediately
                process_completed_task(task)

        def process_completed_task(task):
            for downstream in task.downstream_tasks:
                in_degree[downstream.name] -= 1
                if in_degree[downstream.name] == 0:
                    process_ready_task(downstream)

        # Initial submission
        while ready_tasks:
            task = ready_tasks.popleft()
            process_ready_task(task)

        # Wait for futures
        while active_futures:
            # wait_for_completion returns dict of {task_name: {status, result/error}}
            # and removes done futures from active_futures (passed by ref? No, we passed keys?)
            # My implementation of wait_for_completion modifies the dict if it pops?
            # Let's check implementation. LocalExecutor pops.
            
            completed_info = self.executor.wait_for_completion(active_futures)
            
            for task_name, info in completed_info.items():
                task = self.tasks[task_name]
                status = info["status"]
                
                if status == "SUCCESS":
                    task_status[task.name] = "SUCCESS"
                    self.backend.update_task_status(run_id, task.name, "SUCCESS")
                    pipeline_context[task.name] = info["result"]
                else:
                    print(f"Task {task.name} failed: {info.get('error')}")
                    task_status[task.name] = "FAILED"
                    self.backend.update_task_status(run_id, task.name, "FAILED")
                
                process_completed_task(task)

        print(f"Pipeline {self.name} finished.")
        
        # Check for unfinished tasks (cycles)
        if any(s == "PENDING" for s in task_status.values()):
            raise ValueError("Pipeline contains a cycle (circular dependency) or tasks were not reachable.")

        # Update final run status
        end_time = time.time()
        final_status = "SUCCESS" if all(s in ["SUCCESS", "SKIPPED"] for s in task_status.values()) else "FAILED"
        
        pipeline_run.end_time = end_time
        pipeline_run.status = final_status
        pipeline_run.tasks = task_status
        self.backend.save_run(pipeline_run)
        
        return pipeline_context

    def _evaluate_trigger_rule(self, task: Task, task_status: Dict[str, str]) -> bool:
        """
        Evaluates whether a task should run based on its trigger rule and upstream statuses.
        """
        if not task.upstream_tasks:
            return True # Roots always run

        upstream_statuses = [task_status[t.name] for t in task.upstream_tasks]
        
        if task.trigger_rule == "all_success":
            return all(s == "SUCCESS" for s in upstream_statuses)
        elif task.trigger_rule == "one_failed":
            return any(s == "FAILED" for s in upstream_statuses)
        elif task.trigger_rule == "all_done":
            return all(s in ["SUCCESS", "FAILED", "SKIPPED"] for s in upstream_statuses)
        else:
            return all(s == "SUCCESS" for s in upstream_statuses)

    def _propagate_skip(self, task: Task, task_status: Dict[str, str], in_degree: Dict[str, int]):
        # Deprecated/Unused in new logic
        pass

    def visualize(self, output_file: Optional[str] = None):
        """Generates a Mermaid graph definition."""
        lines = ["graph TD"]
        for task in self.tasks.values():
            # Sanitize names for mermaid
            safe_name = task.name.replace(" ", "_")
            lines.append(f"    {safe_name}[{task.name}]")
            for downstream in task.downstream_tasks:
                safe_down = downstream.name.replace(" ", "_")
                lines.append(f"    {safe_name} --> {safe_down}")
        
        chart = "\n".join(lines)
        if output_file:
            with open(output_file, "w") as f:
                f.write(chart)
        return chart



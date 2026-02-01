from typing import Any, Dict, Optional
from ..task import Task
from ...builder import DremioBuilder

class DremioBuilderTask(Task):
    """
    Task to execute DremioBuilder operations (create, insert, merge, etc.).
    
    Args:
        name: Task name.
        builder: DremioBuilder instance configured with the desired query/transformation.
        command: The operation to perform ('create', 'insert', 'merge', 'delete', 'update').
        target: The target table name (required for create, insert, merge).
        options: Additional arguments for the command (e.g., 'on', 'matched_update' for merge).
    """
    def __init__(self, name: str, builder: DremioBuilder, command: str, target: Optional[str] = None, options: Optional[Dict[str, Any]] = None):
        # Pass dummy action
        super().__init__(name, lambda ctx: None)
        self.builder = builder
        self.command = command.lower()
        self.target = target
        self.options = options or {}
        
        if self.command not in ['create', 'insert', 'merge', 'delete', 'update']:
            raise ValueError(f"Unsupported command: {self.command}")

        if self.command in ['create', 'insert', 'merge'] and not self.target:
            raise ValueError(f"Target table is required for command '{self.command}'")

    def run(self, context: Dict[str, Any]):
        print(f"[{self.name}] Executing Builder command: {self.command}")
        
        try:
            if self.command == "create":
                result = self.builder.create(self.target, **self.options)
            elif self.command == "insert":
                result = self.builder.insert(self.target, **self.options)
            elif self.command == "merge":
                if "on" not in self.options:
                    raise ValueError("Merge requires 'on' option")
                result = self.builder.merge(self.target, **self.options)
            elif self.command == "delete":
                # For delete/update, target is implicit in builder path usually, 
                # but if builder was created from SQL, it might be tricky.
                # However, builder.delete() uses self.path.
                # If user passed target, maybe we should verify?
                # Let's assume builder is configured correctly.
                result = self.builder.delete()
            elif self.command == "update":
                if "updates" not in self.options:
                    raise ValueError("Update requires 'updates' option")
                result = self.builder.update(self.options["updates"])
            else:
                raise ValueError(f"Unsupported command: {self.command}")
            
            self.status = "SUCCESS"
            return result
            
        except Exception as e:
            self.status = "FAILED"
            raise e

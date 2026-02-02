from ..task import Task
import subprocess
import os

class DbtTask(Task):
    """
    Task to execute dbt commands.
    Requires dbt to be installed and available in the PATH.
    """
    def __init__(self, name: str, command: str = "run", project_dir: str = ".", 
                 profiles_dir: str = None, select: str = None, vars: dict = None, **kwargs):
        """
        Args:
            name: Task name.
            command: dbt command (e.g., "run", "test", "seed").
            project_dir: Path to dbt project directory.
            profiles_dir: Path to dbt profiles directory.
            select: dbt select argument (e.g., "my_model+").
            vars: Dictionary of variables to pass to dbt.
        """
        super().__init__(name, self._run_dbt, **kwargs)
        self.command = command
        self.project_dir = project_dir
        self.profiles_dir = profiles_dir
        self.select = select
        self.vars = vars
        self.process = None

    def _run_dbt(self, context=None):
        cmd = ["dbt", self.command]
        
        if self.project_dir:
            cmd.extend(["--project-dir", self.project_dir])
            
        if self.profiles_dir:
            cmd.extend(["--profiles-dir", self.profiles_dir])
            
        if self.select:
            cmd.extend(["--select", self.select])
            
        if self.vars:
            import json
            cmd.extend(["--vars", json.dumps(self.vars)])
            
        print(f"[{self.name}] Executing: {' '.join(cmd)}")
        
        try:
            # Run dbt command
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.project_dir # Run in project dir
            )
            
            stdout, stderr = self.process.communicate()
            
            print(stdout)
            if stderr:
                print(stderr)
                
            if self.process.returncode != 0:
                raise Exception(f"dbt command failed with return code {self.process.returncode}")
                
            self.status = "SUCCESS"
            return stdout
            
        except Exception as e:
            self.status = "FAILED"
            raise e

    def on_kill(self):
        if self.process:
            print(f"[{self.name}] Terminating dbt process...")
            self.process.terminate()

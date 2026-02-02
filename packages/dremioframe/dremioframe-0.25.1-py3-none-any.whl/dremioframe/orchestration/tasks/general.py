import subprocess
import smtplib
import os
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from ..task import Task

class HttpTask(Task):
    """
    Task to perform HTTP requests.
    Requires `requests` library (already a dependency).
    """
    def __init__(self, name: str, url: str, method: str = "GET", headers: Dict = None, json_data: Dict = None, **kwargs):
        import requests
        
        def action(context):
            response = requests.request(method, url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json() if response.content else None
            
        super().__init__(name, action, **kwargs)

class EmailTask(Task):
    """
    Task to send emails via SMTP.
    """
    def __init__(self, name: str, subject: str, body: str, to_addr: str, 
                 smtp_server: str = "localhost", smtp_port: int = 25, 
                 from_addr: str = None, use_tls: bool = False, 
                 username: str = None, password: str = None, **kwargs):
        
        def action(context):
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = from_addr or "dremioframe@localhost"
            msg['To'] = to_addr
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
            return "Email sent"
            
        super().__init__(name, action, **kwargs)

class ShellTask(Task):
    """
    Task to execute shell commands.
    """
    def __init__(self, name: str, command: str, cwd: str = None, env: Dict = None, **kwargs):
        
        def action(context):
            # Merge env with os.environ
            run_env = os.environ.copy()
            if env:
                run_env.update(env)
                
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd, 
                env=run_env, 
                check=True, 
                capture_output=True, 
                text=True
            )
            return result.stdout.strip()
            
        super().__init__(name, action, **kwargs)

class S3Task(Task):
    """
    Task to interact with S3.
    Requires `boto3`.
    Supported operations: 'upload_file', 'download_file'
    """
    def __init__(self, name: str, operation: str, bucket: str, key: str, local_path: str, 
                 aws_access_key_id: str = None, aws_secret_access_key: str = None, 
                 region_name: str = None, endpoint_url: str = None, **kwargs):
        
        def action(context):
            try:
                import boto3
            except ImportError:
                raise ImportError("boto3 is required for S3Task. Install with `pip install dremioframe[s3]`")

            s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=aws_secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name=region_name or os.environ.get("AWS_DEFAULT_REGION"),
                endpoint_url=endpoint_url
            )
            
            if operation == 'upload_file':
                s3.upload_file(local_path, bucket, key)
                return f"Uploaded {local_path} to s3://{bucket}/{key}"
            elif operation == 'download_file':
                s3.download_file(bucket, key, local_path)
                return f"Downloaded s3://{bucket}/{key} to {local_path}"
            else:
                raise ValueError(f"Unsupported S3 operation: {operation}")
                
        super().__init__(name, action, **kwargs)

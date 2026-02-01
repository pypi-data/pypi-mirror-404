import abc
import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
import os
from dataclasses import dataclass, asdict

@dataclass
class PipelineRun:
    pipeline_name: str
    run_id: str
    start_time: float
    status: str # RUNNING, SUCCESS, FAILED
    end_time: Optional[float] = None
    tasks: Dict[str, str] = None # task_name -> status

class BaseBackend(abc.ABC):
    """Abstract base class for orchestration backends."""

    @abc.abstractmethod
    def save_run(self, run: PipelineRun):
        """Saves or updates a pipeline run."""
        pass

    @abc.abstractmethod
    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """Retrieves a pipeline run by ID."""
        pass
    
    @abc.abstractmethod
    def update_task_status(self, run_id: str, task_name: str, status: str):
        """Updates the status of a specific task in a run."""
        pass

    @abc.abstractmethod
    def list_runs(self, pipeline_name: str = None, limit: int = 10) -> List[PipelineRun]:
        """Lists recent pipeline runs."""
        pass

class InMemoryBackend(BaseBackend):
    """In-memory backend (default). State is lost when process exits."""
    
    def __init__(self):
        self.runs: Dict[str, PipelineRun] = {}

    def save_run(self, run: PipelineRun):
        self.runs[run.run_id] = run

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        return self.runs.get(run_id)

    def update_task_status(self, run_id: str, task_name: str, status: str):
        run = self.runs.get(run_id)
        if run:
            if run.tasks is None:
                run.tasks = {}
            run.tasks[task_name] = status

    def list_runs(self, pipeline_name: str = None, limit: int = 10) -> List[PipelineRun]:
        runs = list(self.runs.values())
        if pipeline_name:
            runs = [r for r in runs if r.pipeline_name == pipeline_name]
        # Sort by start time desc
        runs.sort(key=lambda x: x.start_time, reverse=True)
        return runs[:limit]

class SQLiteBackend(BaseBackend):
    """SQLite backend for persistent state."""
    
    def __init__(self, db_path: str = "dremioframe_orchestration.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    pipeline_name TEXT,
                    start_time REAL,
                    end_time REAL,
                    status TEXT,
                    tasks TEXT
                )
            """)

    def save_run(self, run: PipelineRun):
        tasks_json = json.dumps(run.tasks) if run.tasks else "{}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO runs (run_id, pipeline_name, start_time, end_time, status, tasks)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (run.run_id, run.pipeline_name, run.start_time, run.end_time, run.status, tasks_json))

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                return PipelineRun(
                    run_id=row[0],
                    pipeline_name=row[1],
                    start_time=row[2],
                    end_time=row[3],
                    status=row[4],
                    tasks=json.loads(row[5]) if row[5] else {}
                )
        return None

    def update_task_status(self, run_id: str, task_name: str, status: str):
        # SQLite doesn't support partial JSON updates easily without extensions,
        # so we read-modify-write. Transactional safety is important here.
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT tasks FROM runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                tasks = json.loads(row[0]) if row[0] else {}
                tasks[task_name] = status
                conn.execute("UPDATE runs SET tasks = ? WHERE run_id = ?", (json.dumps(tasks), run_id))

    def list_runs(self, pipeline_name: str = None, limit: int = 10) -> List[PipelineRun]:
        query = "SELECT * FROM runs"
        params = []
        if pipeline_name:
            query += " WHERE pipeline_name = ?"
            params.append(pipeline_name)
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        runs = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            for row in cursor:
                runs.append(PipelineRun(
                    run_id=row[0],
                    pipeline_name=row[1],
                    start_time=row[2],
                    end_time=row[3],
                    status=row[4],
                    tasks=json.loads(row[5]) if row[5] else {}
                ))
        return runs

class PostgresBackend(BaseBackend):
    """
    PostgreSQL backend for persistent state.
    Requires `psycopg2-binary` to be installed.
    """
    def __init__(self, dsn: str = None, table_name: str = "dremioframe_runs"):
        try:
            import psycopg2
            from psycopg2.extras import Json
        except ImportError:
            raise ImportError("psycopg2-binary is required for PostgresBackend. Install with `pip install dremioframe[postgres]`")
        
        self.dsn = dsn or os.environ.get("DREMIOFRAME_PG_DSN")
        if not self.dsn:
            raise ValueError("Postgres DSN must be provided or set in DREMIOFRAME_PG_DSN env var.")
        self.table_name = table_name
        self._init_db()

    def _get_conn(self):
        import psycopg2
        return psycopg2.connect(self.dsn)

    def _init_db(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        run_id TEXT PRIMARY KEY,
                        pipeline_name TEXT,
                        start_time DOUBLE PRECISION,
                        end_time DOUBLE PRECISION,
                        status TEXT,
                        tasks JSONB
                    )
                """)
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_pipeline ON {self.table_name} (pipeline_name)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_start_time ON {self.table_name} (start_time DESC)")
            conn.commit()
        finally:
            conn.close()

    def save_run(self, run: PipelineRun):
        from psycopg2.extras import Json
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.table_name} (run_id, pipeline_name, start_time, end_time, status, tasks)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        pipeline_name = EXCLUDED.pipeline_name,
                        start_time = EXCLUDED.start_time,
                        end_time = EXCLUDED.end_time,
                        status = EXCLUDED.status,
                        tasks = EXCLUDED.tasks
                """, (run.run_id, run.pipeline_name, run.start_time, run.end_time, run.status, Json(run.tasks or {})))
            conn.commit()
        finally:
            conn.close()

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {self.table_name} WHERE run_id = %s", (run_id,))
                row = cur.fetchone()
                if row:
                    # row: run_id, pipeline_name, start_time, end_time, status, tasks
                    return PipelineRun(
                        run_id=row[0],
                        pipeline_name=row[1],
                        start_time=row[2],
                        end_time=row[3],
                        status=row[4],
                        tasks=row[5] if row[5] else {}
                    )
        finally:
            conn.close()
        return None

    def update_task_status(self, run_id: str, task_name: str, status: str):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                # Use jsonb_set to update a specific key in the JSONB column
                # jsonb_set(target, path, new_value, create_missing)
                cur.execute(f"""
                    UPDATE {self.table_name}
                    SET tasks = jsonb_set(COALESCE(tasks, '{{}}'::jsonb), %s, %s, true)
                    WHERE run_id = %s
                """, ([task_name], f'"{status}"', run_id))
            conn.commit()
        finally:
            conn.close()

    def list_runs(self, pipeline_name: str = None, limit: int = 10) -> List[PipelineRun]:
        query = f"SELECT * FROM {self.table_name}"
        params = []
        if pipeline_name:
            query += " WHERE pipeline_name = %s"
            params.append(pipeline_name)
        
        query += " ORDER BY start_time DESC LIMIT %s"
        params.append(limit)
        
        runs = []
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                for row in cur:
                    runs.append(PipelineRun(
                        run_id=row[0],
                        pipeline_name=row[1],
                        start_time=row[2],
                        end_time=row[3],
                        status=row[4],
                        tasks=row[5] if row[5] else {}
                    ))
        finally:
            conn.close()
        return runs

class MySQLBackend(BaseBackend):
    """
    MySQL backend for persistent state.
    Requires `mysql-connector-python` to be installed.
    """
    def __init__(self, config: Dict[str, Any] = None, table_name: str = "dremioframe_runs"):
        try:
            import mysql.connector
        except ImportError:
            raise ImportError("mysql-connector-python is required for MySQLBackend. Install with `pip install dremioframe[mysql]`")
        
        self.config = config or {}
        # Fallback to env vars if config not provided
        if not self.config:
            self.config = {
                "user": os.environ.get("DREMIOFRAME_MYSQL_USER"),
                "password": os.environ.get("DREMIOFRAME_MYSQL_PASSWORD"),
                "host": os.environ.get("DREMIOFRAME_MYSQL_HOST", "localhost"),
                "database": os.environ.get("DREMIOFRAME_MYSQL_DB"),
                "port": int(os.environ.get("DREMIOFRAME_MYSQL_PORT", 3306))
            }
        
        if not self.config.get("user") or not self.config.get("database"):
             raise ValueError("MySQL config (user, database) must be provided or set in env vars.")

        self.table_name = table_name
        self._init_db()

    def _get_conn(self):
        import mysql.connector
        return mysql.connector.connect(**self.config)

    def _init_db(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        run_id VARCHAR(255) PRIMARY KEY,
                        pipeline_name VARCHAR(255),
                        start_time DOUBLE,
                        end_time DOUBLE,
                        status VARCHAR(50),
                        tasks JSON
                    )
                """)
                # Index creation might fail if exists in some mysql versions without IF NOT EXISTS procedure, 
                # but let's try simple approach or ignore error
                try:
                    cur.execute(f"CREATE INDEX idx_{self.table_name}_pipeline ON {self.table_name} (pipeline_name)")
                except Exception:
                    pass # Index likely exists
                
                try:
                    cur.execute(f"CREATE INDEX idx_{self.table_name}_start_time ON {self.table_name} (start_time DESC)")
                except Exception:
                    pass
            conn.commit()
        finally:
            conn.close()

    def save_run(self, run: PipelineRun):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                tasks_json = json.dumps(run.tasks) if run.tasks else "{}"
                cur.execute(f"""
                    INSERT INTO {self.table_name} (run_id, pipeline_name, start_time, end_time, status, tasks)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        pipeline_name = VALUES(pipeline_name),
                        start_time = VALUES(start_time),
                        end_time = VALUES(end_time),
                        status = VALUES(status),
                        tasks = VALUES(tasks)
                """, (run.run_id, run.pipeline_name, run.start_time, run.end_time, run.status, tasks_json))
            conn.commit()
        finally:
            conn.close()

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {self.table_name} WHERE run_id = %s", (run_id,))
                row = cur.fetchone()
                if row:
                    # row: run_id, pipeline_name, start_time, end_time, status, tasks
                    # MySQL connector returns tuples
                    return PipelineRun(
                        run_id=row[0],
                        pipeline_name=row[1],
                        start_time=row[2],
                        end_time=row[3],
                        status=row[4],
                        tasks=json.loads(row[5]) if row[5] else {}
                    )
        finally:
            conn.close()
        return None

    def update_task_status(self, run_id: str, task_name: str, status: str):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                # MySQL 5.7+ supports JSON_SET
                # JSON_SET(json_doc, path, val)
                # Path must start with $
                path = f'$."{task_name}"'
                cur.execute(f"""
                    UPDATE {self.table_name}
                    SET tasks = JSON_SET(COALESCE(tasks, '{{}}'), %s, %s)
                    WHERE run_id = %s
                """, (path, status, run_id))
            conn.commit()
        finally:
            conn.close()

    def list_runs(self, pipeline_name: str = None, limit: int = 10) -> List[PipelineRun]:
        query = f"SELECT * FROM {self.table_name}"
        params = []
        if pipeline_name:
            query += " WHERE pipeline_name = %s"
            params.append(pipeline_name)
        
        query += " ORDER BY start_time DESC LIMIT %s"
        params.append(limit)
        
        runs = []
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                for row in cur:
                    runs.append(PipelineRun(
                        run_id=row[0],
                        pipeline_name=row[1],
                        start_time=row[2],
                        end_time=row[3],
                        status=row[4],
                        tasks=json.loads(row[5]) if row[5] else {}
                    ))
        finally:
            conn.close()
        return runs

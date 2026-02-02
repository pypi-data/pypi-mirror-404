from typing import Any, Dict, Optional, Sequence, Union
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from .hooks import DremioHook

class DremioSQLOperator(BaseOperator):
    """
    Executes SQL code in Dremio.
    
    :param sql: The SQL code to execute.
    :param dremio_conn_id: The connection ID to use.
    :param return_result: Whether to return the result (as XCom). Default False (to avoid large XComs).
    """
    template_fields: Sequence[str] = ("sql",)
    template_ext: Sequence[str] = (".sql",)
    ui_color = "#ededed"

    @apply_defaults
    def __init__(
        self,
        sql: str,
        dremio_conn_id: str = "dremio_default",
        return_result: bool = False,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.sql = sql
        self.dremio_conn_id = dremio_conn_id
        self.return_result = return_result

    def execute(self, context: Dict[str, Any]) -> Any:
        hook = DremioHook(dremio_conn_id=self.dremio_conn_id)
        self.log.info(f"Executing SQL: {self.sql}")
        
        # We use get_pandas_df to get the result
        df = hook.get_pandas_df(self.sql)
        
        self.log.info(f"Query returned {len(df)} rows.")
        
        if self.return_result:
            return df.to_dict(orient="records")
        return None

class DremioDataQualityOperator(BaseOperator):
    """
    Runs a data quality check on a Dremio table.
    
    :param table_name: The table to check.
    :param checks: A list of checks to run. Each check is a dict with 'type' and args.
                   Example: [{"type": "not_null", "column": "id"}, {"type": "row_count", "expr": "val > 0", "value": 5, "op": "ge"}]
    :param dremio_conn_id: The connection ID to use.
    """
    template_fields: Sequence[str] = ("table_name",)
    ui_color = "#f4a460"

    @apply_defaults
    def __init__(
        self,
        table_name: str,
        checks: Sequence[Dict[str, Any]],
        dremio_conn_id: str = "dremio_default",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.table_name = table_name
        self.checks = checks
        self.dremio_conn_id = dremio_conn_id

    def execute(self, context: Dict[str, Any]) -> Any:
        hook = DremioHook(dremio_conn_id=self.dremio_conn_id)
        client = hook.get_conn()
        builder = client.table(self.table_name)
        dq = builder.quality
        
        self.log.info(f"Running data quality checks on {self.table_name}...")
        
        failed_checks = []
        
        for check in self.checks:
            check_type = check.get("type")
            try:
                if check_type == "not_null":
                    dq.expect_not_null(check["column"])
                elif check_type == "unique":
                    dq.expect_unique(check["column"])
                elif check_type == "row_count":
                    dq.expect_row_count(check["expr"], check["value"], check.get("op", "eq"))
                elif check_type == "values_in":
                    dq.expect_values_in(check["column"], check["values"])
                else:
                    self.log.warning(f"Unknown check type: {check_type}")
                    continue
                
                self.log.info(f"Check passed: {check}")
            except AssertionError as e:
                self.log.error(f"Check failed: {check} - {e}")
                failed_checks.append((check, str(e)))
            except Exception as e:
                self.log.error(f"Check error: {check} - {e}")
                failed_checks.append((check, str(e)))
                
        if failed_checks:
            raise ValueError(f"Data Quality Checks Failed: {failed_checks}")
            
        self.log.info("All data quality checks passed.")

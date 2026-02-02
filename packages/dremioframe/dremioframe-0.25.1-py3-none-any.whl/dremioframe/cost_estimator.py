from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
from dremioframe.client import DremioClient

@dataclass
class CostEstimate:
    """Represents estimated cost metrics for a query"""
    estimated_rows: int
    estimated_bytes: int
    scan_cost: float
    join_cost: float
    total_cost: float
    plan_summary: str
    optimization_hints: List[str]

@dataclass
class OptimizationHint:
    """Represents a query optimization suggestion"""
    severity: str  # 'info', 'warning', 'critical'
    category: str  # 'filter', 'join', 'reflection', 'partition'
    message: str
    suggestion: str

class CostEstimator:
    """
    Analyzes query execution plans to estimate costs and suggest optimizations.
    """
    def __init__(self, client: DremioClient):
        self.client = client

    def estimate_query_cost(self, sql: str) -> CostEstimate:
        """
        Estimate the cost of executing a query.
        Uses EXPLAIN PLAN to analyze the query execution plan.
        """
        # Get the query plan using REST API (EXPLAIN doesn't work with Flight SQL)
        explain_sql = f"EXPLAIN PLAN FOR {sql}"
        
        try:
            # Use REST API endpoint for SQL execution
            import requests
            response = requests.post(
                f"{self.client.base_url}/sql",
                headers=self.client.headers,
                json={"sql": explain_sql}
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract plan text from response
            if 'rows' in result and len(result['rows']) > 0:
                plan_text = result['rows'][0].get('PLAN', '') or result['rows'][0].get('text', '')
            else:
                plan_text = ""
        except Exception as e:
            # Fallback: return empty metrics if EXPLAIN fails
            plan_text = ""
            print(f"Warning: Could not get EXPLAIN plan: {e}")
        
        # Extract metrics from plan
        metrics = self._parse_plan_metrics(plan_text)
        
        # Generate optimization hints
        hints = self.get_optimization_hints(sql, plan_text)
        
        return CostEstimate(
            estimated_rows=metrics.get('rows', 0),
            estimated_bytes=metrics.get('bytes', 0),
            scan_cost=metrics.get('scan_cost', 0.0),
            join_cost=metrics.get('join_cost', 0.0),
            total_cost=metrics.get('total_cost', 0.0),
            plan_summary=self._summarize_plan(plan_text),
            optimization_hints=[h.message for h in hints]
        )

    def _parse_plan_metrics(self, plan_text: str) -> Dict[str, Any]:
        """
        Parse metrics from the EXPLAIN PLAN output.
        Dremio's plan format includes cost estimates.
        """
        metrics = {
            'rows': 0,
            'bytes': 0,
            'scan_cost': 0.0,
            'join_cost': 0.0,
            'total_cost': 0.0
        }
        
        # Extract row estimates (look for patterns like "rowcount = 1000")
        row_match = re.search(r'rowcount\s*=\s*(\d+\.?\d*)', plan_text, re.IGNORECASE)
        if row_match:
            metrics['rows'] = int(float(row_match.group(1)))
        
        # Extract cost estimates (look for patterns like "cost = {123.45}")
        cost_matches = re.findall(r'cost\s*=?\s*\{?(\d+\.?\d*)', plan_text, re.IGNORECASE)
        if cost_matches:
            costs = [float(c) for c in cost_matches]
            metrics['total_cost'] = sum(costs)
        
        # Identify scan operations
        scan_count = len(re.findall(r'Scan|TableScan', plan_text, re.IGNORECASE))
        metrics['scan_cost'] = scan_count * 10.0  # Arbitrary weight
        
        # Identify join operations
        join_count = len(re.findall(r'Join|HashJoin|MergeJoin', plan_text, re.IGNORECASE))
        metrics['join_cost'] = join_count * 50.0  # Joins are more expensive
        
        # Estimate bytes (rough approximation)
        metrics['bytes'] = metrics['rows'] * 100  # Assume ~100 bytes per row
        
        return metrics

    def _summarize_plan(self, plan_text: str) -> str:
        """Create a human-readable summary of the query plan"""
        operations = []
        
        if 'Scan' in plan_text or 'TableScan' in plan_text:
            scan_count = len(re.findall(r'Scan|TableScan', plan_text, re.IGNORECASE))
            operations.append(f"{scan_count} table scan(s)")
        
        if 'Join' in plan_text:
            join_count = len(re.findall(r'Join', plan_text, re.IGNORECASE))
            operations.append(f"{join_count} join(s)")
        
        if 'Aggregate' in plan_text or 'Agg' in plan_text:
            operations.append("aggregation")
        
        if 'Sort' in plan_text:
            operations.append("sorting")
        
        if 'Filter' in plan_text:
            filter_count = len(re.findall(r'Filter', plan_text, re.IGNORECASE))
            operations.append(f"{filter_count} filter(s)")
        
        return "Query plan includes: " + ", ".join(operations) if operations else "Simple query"

    def get_optimization_hints(self, sql: str, plan_text: str = None) -> List[OptimizationHint]:
        """
        Analyze SQL and plan to provide optimization suggestions.
        """
        hints = []
        
        # Get plan if not provided
        if plan_text is None:
            try:
                explain_sql = f"EXPLAIN PLAN FOR {sql}"
                plan_df = self.client.sql(explain_sql).collect()
                plan_text = plan_df.iloc[0, 0] if not plan_df.empty else ""
            except:
                plan_text = ""
        
        # Check for SELECT *
        if re.search(r'SELECT\s+\*', sql, re.IGNORECASE):
            hints.append(OptimizationHint(
                severity='warning',
                category='projection',
                message="Query uses SELECT *",
                suggestion="Specify only the columns you need to reduce data transfer and improve performance"
            ))
        
        # Check for missing WHERE clause on large scans
        if 'WHERE' not in sql.upper() and 'Scan' in plan_text:
            hints.append(OptimizationHint(
                severity='warning',
                category='filter',
                message="Query may be scanning entire table without filters",
                suggestion="Add WHERE clause to filter data early and reduce rows processed"
            ))
        
        # Check for multiple joins
        join_count = len(re.findall(r'Join', plan_text, re.IGNORECASE))
        if join_count > 3:
            hints.append(OptimizationHint(
                severity='info',
                category='join',
                message=f"Query has {join_count} joins",
                suggestion="Consider breaking complex joins into CTEs or temp tables for better readability and potential optimization"
            ))
        
        # Check for DISTINCT without GROUP BY
        if 'DISTINCT' in sql.upper() and 'GROUP BY' not in sql.upper():
            hints.append(OptimizationHint(
                severity='info',
                category='aggregation',
                message="Query uses DISTINCT",
                suggestion="If you're counting distinct values, consider using COUNT(DISTINCT col) or GROUP BY instead"
            ))
        
        # Check for ORDER BY without LIMIT
        if 'ORDER BY' in sql.upper() and 'LIMIT' not in sql.upper():
            hints.append(OptimizationHint(
                severity='info',
                category='sorting',
                message="Query has ORDER BY without LIMIT",
                suggestion="If you only need top N results, add LIMIT clause to avoid sorting entire result set"
            ))
        
        return hints

    def compare_queries(self, *sqls: str) -> Dict[str, Any]:
        """
        Compare cost estimates for multiple query variations.
        Returns a comparison report recommending the best approach.
        """
        results = []
        
        for i, sql in enumerate(sqls):
            try:
                estimate = self.estimate_query_cost(sql)
                results.append({
                    'query_id': i + 1,
                    'sql': sql[:100] + '...' if len(sql) > 100 else sql,
                    'total_cost': estimate.total_cost,
                    'estimated_rows': estimate.estimated_rows,
                    'plan_summary': estimate.plan_summary,
                    'hints_count': len(estimate.optimization_hints)
                })
            except Exception as e:
                results.append({
                    'query_id': i + 1,
                    'sql': sql[:100] + '...' if len(sql) > 100 else sql,
                    'error': str(e)
                })
        
        # Find best query (lowest cost)
        valid_results = [r for r in results if 'error' not in r]
        if valid_results:
            best = min(valid_results, key=lambda x: x['total_cost'])
            recommendation = f"Query {best['query_id']} has the lowest estimated cost ({best['total_cost']:.2f})"
        else:
            recommendation = "Unable to determine best query - all queries failed"
        
        return {
            'queries': results,
            'recommendation': recommendation,
            'best_query_id': best['query_id'] if valid_results else None
        }

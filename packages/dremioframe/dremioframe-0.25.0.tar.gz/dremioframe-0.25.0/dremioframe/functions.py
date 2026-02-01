from typing import Union, List, Any

class Expr(str):
    """
    Represents a SQL expression.
    Inherits from str so it can be used directly in SQL strings.
    """
    def __new__(cls, content):
        return super().__new__(cls, content)

    def alias(self, name: str) -> 'Expr':
        return Expr(f"{self} AS {name}")
    
    def cast(self, type_: str) -> 'Expr':
        return Expr(f"CAST({self} AS {type_})")
    
    def over(self, window: 'WindowSpec') -> 'Expr':
        return Expr(f"{self} OVER ({window})")

    # Arithmetic Operators
    def __add__(self, other):
        return Expr(f"({self} + {other})")
    
    def __sub__(self, other):
        return Expr(f"({self} - {other})")
    
    def __mul__(self, other):
        return Expr(f"({self} * {other})")
    
    def __truediv__(self, other):
        return Expr(f"({self} / {other})")
    
    def __mod__(self, other):
        return Expr(f"({self} % {other})")

    # Comparison Operators
    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        return Expr(f"({self} = {self._fmt_val(other)})")
    
    def __ne__(self, other):
        return Expr(f"({self} <> {self._fmt_val(other)})")
    
    def __gt__(self, other):
        return Expr(f"({self} > {self._fmt_val(other)})")
    
    def __lt__(self, other):
        return Expr(f"({self} < {self._fmt_val(other)})")
    
    def __ge__(self, other):
        return Expr(f"({self} >= {self._fmt_val(other)})")
    
    def __le__(self, other):
        return Expr(f"({self} <= {self._fmt_val(other)})")

    # Logical Operators
    def __and__(self, other):
        return Expr(f"({self} AND {other})")
    
    def __or__(self, other):
        return Expr(f"({self} OR {other})")
    
    def __invert__(self):
        return Expr(f"(NOT {self})")
    
    def is_null(self):
        return Expr(f"({self} IS NULL)")
    
    def is_not_null(self):
        return Expr(f"({self} IS NOT NULL)")
    
    def isin(self, values: List[Any]):
        vals = ", ".join([self._fmt_val(v) for v in values])
        return Expr(f"({self} IN ({vals}))")

    def _fmt_val(self, val):
        if isinstance(val, str) and not isinstance(val, Expr):
            return f"'{val}'"
        if val is None:
            return "NULL"
        return str(val)

class WindowSpec:
    def __init__(self):
        self._partition_by = []
        self._order_by = []
        self._frame = None

    def partition_by(self, *cols) -> 'WindowSpec':
        self._partition_by.extend(cols)
        return self

    def order_by(self, *cols) -> 'WindowSpec':
        self._order_by.extend(cols)
        return self
    
    def rows_between(self, start, end) -> 'WindowSpec':
        self._frame = f"ROWS BETWEEN {start} AND {end}"
        return self
    
    def range_between(self, start, end) -> 'WindowSpec':
        self._frame = f"RANGE BETWEEN {start} AND {end}"
        return self

    def __str__(self):
        parts = []
        if self._partition_by:
            parts.append(f"PARTITION BY {', '.join(map(str, self._partition_by))}")
        if self._order_by:
            parts.append(f"ORDER BY {', '.join(map(str, self._order_by))}")
        if self._frame:
            parts.append(self._frame)
        return " ".join(parts)

class Window:
    @staticmethod
    def partition_by(*cols) -> WindowSpec:
        return WindowSpec().partition_by(*cols)
    
    @staticmethod
    def order_by(*cols) -> WindowSpec:
        return WindowSpec().order_by(*cols)

# --- Functions ---

def col(name: str) -> Expr:
    return Expr(name)

def lit(val: Any) -> Expr:
    if isinstance(val, str):
        return Expr(f"'{val}'")
    if val is None:
        return Expr("NULL")
    return Expr(str(val))

# Aggregates
def sum(col) -> Expr: return Expr(f"SUM({col})")
def avg(col) -> Expr: return Expr(f"AVG({col})")
def min(col) -> Expr: return Expr(f"MIN({col})")
def max(col) -> Expr: return Expr(f"MAX({col})")
def count(col) -> Expr: return Expr(f"COUNT({col})")
def stddev(col) -> Expr: return Expr(f"STDDEV({col})")
def variance(col) -> Expr: return Expr(f"VARIANCE({col})")
def approx_distinct(col) -> Expr: return Expr(f"APPROX_COUNT_DISTINCT({col})")

# Math
def abs(col) -> Expr: return Expr(f"ABS({col})")
def ceil(col) -> Expr: return Expr(f"CEIL({col})")
def floor(col) -> Expr: return Expr(f"FLOOR({col})")
def round(col, scale=0) -> Expr: return Expr(f"ROUND({col}, {scale})")
def sqrt(col) -> Expr: return Expr(f"SQRT({col})")
def exp(col) -> Expr: return Expr(f"EXP({col})")
def ln(col) -> Expr: return Expr(f"LN({col})")
def log(base, col) -> Expr: return Expr(f"LOG({base}, {col})")
def pow(col, power) -> Expr: return Expr(f"POWER({col}, {power})")

# String
def upper(col) -> Expr: return Expr(f"UPPER({col})")
def lower(col) -> Expr: return Expr(f"LOWER({col})")
def concat(*cols) -> Expr: return Expr(f"CONCAT({', '.join(map(str, cols))})")
def substr(col, start, length=None) -> Expr: 
    if length: return Expr(f"SUBSTR({col}, {start}, {length})")
    return Expr(f"SUBSTR({col}, {start})")
def trim(col) -> Expr: return Expr(f"TRIM({col})")
def ltrim(col) -> Expr: return Expr(f"LTRIM({col})")
def rtrim(col) -> Expr: return Expr(f"RTRIM({col})")
def length(col) -> Expr: return Expr(f"LENGTH({col})")
def replace(col, pattern, replacement) -> Expr: return Expr(f"REPLACE({col}, '{pattern}', '{replacement}')")
def regexp_replace(col, pattern, replacement) -> Expr: return Expr(f"REGEXP_REPLACE({col}, '{pattern}', '{replacement}')")
def initcap(col) -> Expr: return Expr(f"INITCAP({col})")

# Date/Time
def current_date() -> Expr: return Expr("CURRENT_DATE")
def current_timestamp() -> Expr: return Expr("CURRENT_TIMESTAMP")
def date_add(col, days) -> Expr: return Expr(f"DATE_ADD({col}, {days})")
def date_sub(col, days) -> Expr: return Expr(f"DATE_SUB({col}, {days})")
def date_diff(col1, col2) -> Expr: return Expr(f"DATE_DIFF({col1}, {col2})")
def to_date(col, fmt=None) -> Expr: 
    if fmt: return Expr(f"TO_DATE({col}, '{fmt}')")
    return Expr(f"TO_DATE({col})")
def to_timestamp(col, fmt=None) -> Expr:
    if fmt: return Expr(f"TO_TIMESTAMP({col}, '{fmt}')")
    return Expr(f"TO_TIMESTAMP({col})")
def year(col) -> Expr: return Expr(f"YEAR({col})")
def month(col) -> Expr: return Expr(f"MONTH({col})")
def day(col) -> Expr: return Expr(f"DAY({col})")
def hour(col) -> Expr: return Expr(f"HOUR({col})")
def minute(col) -> Expr: return Expr(f"MINUTE({col})")
def second(col) -> Expr: return Expr(f"SECOND({col})")
def extract(field, source) -> Expr: return Expr(f"EXTRACT({field} FROM {source})")

# Conditional
def coalesce(*cols) -> Expr: return Expr(f"COALESCE({', '.join(map(str, cols))})")

class CaseBuilder:
    def __init__(self, condition, value):
        self.cases = [(condition, value)]
        self.else_val = None
    
    def when(self, condition, value):
        self.cases.append((condition, value))
        return self
    
    def otherwise(self, value):
        self.else_val = value
        return self._build()
    
    def _build(self):
        parts = ["CASE"]
        for cond, val in self.cases:
            parts.append(f"WHEN {cond} THEN {val}")
        if self.else_val is not None:
            parts.append(f"ELSE {self.else_val}")
        parts.append("END")
        return Expr(" ".join(parts))
    
    def __str__(self):
        return self._build()

def when(condition, value) -> CaseBuilder:
    return CaseBuilder(condition, value)

# Window Functions
def rank() -> Expr: return Expr("RANK()")
def dense_rank() -> Expr: return Expr("DENSE_RANK()")
def row_number() -> Expr: return Expr("ROW_NUMBER()")
def lead(col, offset=1, default=None) -> Expr: 
    if default is not None: return Expr(f"LEAD({col}, {offset}, {default})")
    return Expr(f"LEAD({col}, {offset})")
def lag(col, offset=1, default=None) -> Expr:
    if default is not None: return Expr(f"LAG({col}, {offset}, {default})")
    return Expr(f"LAG({col}, {offset})")
def first_value(col) -> Expr: return Expr(f"FIRST_VALUE({col})")
def last_value(col) -> Expr: return Expr(f"LAST_VALUE({col})")
def ntile(n) -> Expr: return Expr(f"NTILE({n})")

# AI Functions
def ai_classify(prompt, categories: List[Any], model_name: str = None) -> Expr:
    """
    Classifies text into one of the provided categories.
    """
    cats = ", ".join([f"'{c}'" if isinstance(c, str) else str(c) for c in categories])
    cats_array = f"ARRAY[{cats}]"
    
    if model_name:
        return Expr(f"AI_CLASSIFY('{model_name}', '{prompt}', {cats_array})")
    return Expr(f"AI_CLASSIFY('{prompt}', {cats_array})")

def ai_complete(prompt, model_name: str = None) -> Expr:
    """
    Generates a text completion for the prompt.
    """
    if model_name:
        return Expr(f"AI_COMPLETE('{model_name}', '{prompt}')")
    return Expr(f"AI_COMPLETE('{prompt}')")

def ai_generate(prompt, model_name: str = None, schema: str = None) -> Expr:
    """
    Generates structured data based on the prompt.
    """
    # Handle prompt tuple for file reference? For now assume prompt is string or Expr
    # If schema is provided, append WITH SCHEMA
    
    base = ""
    if model_name:
        base = f"AI_GENERATE('{model_name}', '{prompt}'"
    else:
        base = f"AI_GENERATE('{prompt}'"
        
    if schema:
        base += f" WITH SCHEMA {schema}"
        
    base += ")"
    return Expr(base)

# Complex Types
def flatten(col) -> Expr:
    """
    Explodes a list into multiple rows.
    """
    return Expr(f"FLATTEN({col})")

def convert_from(col, type_: str) -> Expr:
    """
    Convert from a serialized format (e.g. JSON) to a complex type.
    """
    return Expr(f"CONVERT_FROM({col}, '{type_}')")

def convert_to(col, type_: str) -> Expr:
    """
    Convert a complex type to a serialized format (e.g. JSON).
    """
    return Expr(f"CONVERT_TO({col}, '{type_}')")

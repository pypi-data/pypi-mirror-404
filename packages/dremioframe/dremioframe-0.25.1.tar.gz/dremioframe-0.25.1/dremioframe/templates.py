from typing import Dict, Any, Optional
from string import Template

class QueryTemplate:
    """
    Represents a parameterized SQL query template.
    Uses standard Python string.Template syntax ($param or ${param}).
    """
    def __init__(self, sql: str, name: Optional[str] = None, description: Optional[str] = None):
        self.sql = sql
        self.name = name
        self.description = description
        self.template = Template(sql)

    def render(self, **params) -> str:
        """
        Render the template with the given parameters.
        """
        return self.template.safe_substitute(**params)

class TemplateLibrary:
    """
    A collection of query templates.
    """
    def __init__(self):
        self.templates: Dict[str, QueryTemplate] = {}

    def register(self, name: str, sql: str, description: Optional[str] = None):
        """
        Register a new template.
        """
        self.templates[name] = QueryTemplate(sql, name, description)

    def get(self, name: str) -> QueryTemplate:
        """
        Get a template by name.
        """
        if name not in self.templates:
            raise KeyError(f"Template '{name}' not found.")
        return self.templates[name]

    def render(self, name: str, **params) -> str:
        """
        Render a registered template.
        """
        template = self.get(name)
        return template.render(**params)

# Global library instance
library = TemplateLibrary()

# Common templates
library.register(
    "row_count",
    "SELECT COUNT(*) as count FROM $table",
    "Get row count of a table"
)

library.register(
    "sample",
    "SELECT * FROM $table LIMIT $limit",
    "Get sample rows from a table"
)

library.register(
    "distinct_values",
    "SELECT DISTINCT $column FROM $table ORDER BY $column",
    "Get distinct values of a column"
)

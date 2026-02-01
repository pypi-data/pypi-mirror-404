"""
Testing utilities for DremioFrame.

This module provides mock objects and test helpers for writing tests
without requiring a live Dremio connection.
"""

from .mock_client import MockDremioClient
from .fixtures import FixtureManager
from .assertions import (
    assert_dataframes_equal,
    assert_schema_matches,
    assert_query_valid,
    assert_row_count
)

__all__ = [
    'MockDremioClient',
    'FixtureManager',
    'assert_dataframes_equal',
    'assert_schema_matches',
    'assert_query_valid',
    'assert_row_count'
]

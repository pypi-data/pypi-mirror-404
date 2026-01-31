"""Data query backend module.

Provides protocol and implementations for querying data warehouses (DuckDB, Snowflake, etc.)
"""

from .factory import (
    create_data_backend,
    create_data_backend_for_cli,
)
from .protocol import DataQueryBackend

__all__ = [
    # Protocol
    "DataQueryBackend",
    # Factory functions (use unified config)
    "create_data_backend",
    "create_data_backend_for_cli",
]

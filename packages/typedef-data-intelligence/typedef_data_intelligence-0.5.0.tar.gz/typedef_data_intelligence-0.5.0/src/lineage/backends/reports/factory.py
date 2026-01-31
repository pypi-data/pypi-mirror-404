"""Reports backend factory functions.

This module provides factory functions for creating reports backend instances
from configuration objects.
"""
from typing import Optional

from lineage.backends.config import FilesystemReportsConfig, ReportsConfig
from lineage.backends.reports.filesystem import FilesystemReportsBackend
from lineage.backends.reports.protocol import ReportsBackend


def create_reports_backend(config: ReportsConfig) -> Optional[ReportsBackend]:
    """Create a reports backend instance from configuration.

    Args:
        config: Reports backend configuration object.

    Returns:
        Reports backend instance or None.

    Raises:
        ValueError: If the configuration type is not supported.
    """
    if isinstance(config, FilesystemReportsConfig):
        return FilesystemReportsBackend(config.base_path)
    else:
        raise ValueError(f"Unknown reports backend: {type(config)}. Supported: FilesystemReportsConfig.")
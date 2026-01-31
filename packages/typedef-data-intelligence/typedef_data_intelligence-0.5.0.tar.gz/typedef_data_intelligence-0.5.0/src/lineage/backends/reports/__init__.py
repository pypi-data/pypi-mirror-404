"""Reports backend for storing and managing analyst reports."""

from lineage.backends.reports.factory import create_reports_backend
from lineage.backends.reports.filesystem import FilesystemReportsBackend
from lineage.backends.reports.protocol import ReportsBackend

__all__ = ["FilesystemReportsBackend", "ReportsBackend", "create_reports_backend"]

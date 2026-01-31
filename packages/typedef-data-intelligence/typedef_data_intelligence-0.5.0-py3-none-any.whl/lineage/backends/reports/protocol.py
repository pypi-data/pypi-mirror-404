"""Reports backend protocol definitions.

This module defines the protocol interface for reports backends and associated
data models for cells and metadata.
"""
from datetime import datetime
from typing import Any, Dict, List, Protocol

from pydantic import BaseModel


class CellData(BaseModel):
    """Represents a single cell in a report."""

    cell_id: str
    cell_type: str  # markdown, chart, table
    cell_number: int  # 1-indexed position
    data: Dict[str, Any]  # Cell-specific data


class ReportMetadata(BaseModel):
    """Metadata about a saved report."""

    report_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    cell_count: int


class Report(BaseModel):
    """Full report with all cells."""

    report_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    cells: List[CellData]

class ReportsBackend(Protocol):
    """Protocol for reports backend."""

    def create_report(self, title: str) -> str:
        """Create a new report."""
        pass

    def add_cells(self, report_id: str, cells: List[CellData]) -> None:
        """Add cells to a report."""
        pass

    def get_report(self, report_id: str) -> Report:
        """Get a report by its ID."""
        pass

    def list_reports(self) -> List[ReportMetadata]:
        """List all reports."""
        pass

    def delete_report(self, report_id: str) -> None:
        """Delete a report by its ID."""
        pass

    def modify_cell(self, report_id: str, cell_number: int, cell_data: CellData) -> None:
        """Modify an existing cell in a report."""
        pass

    def delete_cell(self, report_id: str, cell_number: int) -> None:
        """Delete a cell and renumber subsequent cells."""
        pass

    def get_cell(self, report_id: str, cell_number: int) -> CellData:
        """Retrieve a specific cell."""
        pass
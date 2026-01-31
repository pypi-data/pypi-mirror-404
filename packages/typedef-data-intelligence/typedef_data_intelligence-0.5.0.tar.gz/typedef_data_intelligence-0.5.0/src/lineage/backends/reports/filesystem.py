"""Filesystem-based storage backend for reports."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from lineage.backends.reports.protocol import (
    CellData,
    Report,
    ReportMetadata,
    ReportsBackend,
)
from lineage.backends.utils import atomic_write_json, ensure_directory

logger = logging.getLogger(__name__)

class FilesystemReportsBackend(ReportsBackend):
    """Filesystem-based storage for reports (similar to tickets backend)."""

    def __init__(self, reports_dir: Path | str = "./reports"):
        """Initialize the filesystem backend.

        Args:
            reports_dir: Directory to store report files
        """
        self.reports_dir = Path(reports_dir)
        ensure_directory(self.reports_dir)

    def create_report(self, title: str) -> str:
        """Create a new empty report.

        Args:
            title: Report title

        Returns:
            report_id: Unique identifier for the report
        """
        report_id = str(uuid.uuid4())
        report_dir = self.reports_dir / report_id
        ensure_directory(report_dir)

        report = Report(
            report_id=report_id,
            title=title,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            cells=[],
        )

        self._save_report(report)
        return report_id

    def add_cells(self, report_id: str, cells: List[CellData]) -> None:
        """Append cells to an existing report.

        Args:
            report_id: Report identifier
            cells: List of CellData objects

        Raises:
            FileNotFoundError: If report doesn't exist
        """
        report = self.get_report(report_id)

        # Assign cell numbers and append
        next_cell_number = len(report.cells) + 1
        for cell in cells:
            # Update cell number to maintain sequential ordering
            cell.cell_number = next_cell_number
            report.cells.append(cell)
            next_cell_number += 1

        report.updated_at = datetime.now()
        self._save_report(report)

    def get_report(self, report_id: str) -> Report:
        """Retrieve a report by ID.

        Args:
            report_id: Report identifier

        Returns:
            Report object with all cells

        Raises:
            FileNotFoundError: If report doesn't exist
        """
        report_path = self.reports_dir / report_id / "report.json"
        if not report_path.exists():
            raise FileNotFoundError(f"Report {report_id} not found")

        with open(report_path) as f:
            data = json.load(f)
            return Report(**data)

    def list_reports(self) -> List[ReportMetadata]:
        """List all saved reports.

        Returns:
            List of report metadata (without full cell data)
        """
        reports = []
        for report_dir in self.reports_dir.iterdir():
            if report_dir.is_dir():
                try:
                    report = self.get_report(report_dir.name)
                    reports.append(
                        ReportMetadata(
                            report_id=report.report_id,
                            title=report.title,
                            created_at=report.created_at,
                            updated_at=report.updated_at,
                            cell_count=len(report.cells),
                        )
                    )
                except Exception as e:
                    logger.error(f"Error getting report {report_dir.name}: {e}")
                    continue

        return sorted(reports, key=lambda r: r.updated_at, reverse=True)

    def delete_report(self, report_id: str) -> None:
        """Delete a report and all its files.

        Args:
            report_id: Report identifier

        Raises:
            FileNotFoundError: If report doesn't exist
        """
        report_dir = self.reports_dir / report_id
        if not report_dir.exists():
            raise FileNotFoundError(f"Report {report_id} not found")

        # Delete all files in report directory
        for file in report_dir.iterdir():
            file.unlink()
        report_dir.rmdir()

    def get_report_dir(self, report_id: str) -> Path:
        """Get the directory path for a report.

        Args:
            report_id: Report identifier

        Returns:
            Path to report directory
        """
        return self.reports_dir / report_id

    def modify_cell(self, report_id: str, cell_number: int, cell_data: CellData) -> None:
        """Modify an existing cell in a report.

        Args:
            report_id: Report identifier
            cell_number: 1-indexed cell position
            cell_data: New cell data

        Raises:
            FileNotFoundError: If report doesn't exist
            IndexError: If cell_number is invalid
        """
        report = self.get_report(report_id)

        # Find cell by cell_number (1-indexed)
        cell_index = None
        for i, cell in enumerate(report.cells):
            if cell.cell_number == cell_number:
                cell_index = i
                break

        if cell_index is None:
            raise IndexError(f"Cell {cell_number} not found in report {report_id}")

        # Update cell but preserve cell_number
        cell_data.cell_number = cell_number
        report.cells[cell_index] = cell_data
        report.updated_at = datetime.now()
        self._save_report(report)

    def delete_cell(self, report_id: str, cell_number: int) -> None:
        """Delete a cell and renumber subsequent cells.

        Args:
            report_id: Report identifier
            cell_number: 1-indexed cell position

        Raises:
            FileNotFoundError: If report doesn't exist
            IndexError: If cell_number is invalid
        """
        report = self.get_report(report_id)

        # Find cell by cell_number
        cell_index = None
        for i, cell in enumerate(report.cells):
            if cell.cell_number == cell_number:
                cell_index = i
                break

        if cell_index is None:
            raise IndexError(f"Cell {cell_number} not found in report {report_id}")

        # Remove cell
        report.cells.pop(cell_index)

        # Renumber subsequent cells
        for i in range(cell_index, len(report.cells)):
            report.cells[i].cell_number = i + 1

        report.updated_at = datetime.now()
        self._save_report(report)

    def get_cell(self, report_id: str, cell_number: int) -> CellData:
        """Retrieve a specific cell.

        Args:
            report_id: Report identifier
            cell_number: 1-indexed cell position

        Returns:
            CellData object

        Raises:
            FileNotFoundError: If report doesn't exist
            IndexError: If cell_number is invalid
        """
        report = self.get_report(report_id)

        # Find cell by cell_number
        for cell in report.cells:
            if cell.cell_number == cell_number:
                return cell

        raise IndexError(f"Cell {cell_number} not found in report {report_id}")

    def _save_report(self, report: Report) -> None:
        """Internal method to save report to disk.

        Args:
            report: Report object to save
        """
        report_path = self.reports_dir / report.report_id / "report.json"
        atomic_write_json(report_path, report.model_dump(mode="json"))

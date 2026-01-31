"""Progress tracking for typedef sync operations.

This module provides a unified progress tracking system for the sync command,
with Rich-based CLI display and a protocol for future TUI integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Protocol

from rich.progress import TaskID


class SyncPhase(Enum):
    """Phases of the sync/ingest process."""

    MANIFEST_PARSING = "Parsing Manifest"
    CHANGE_DETECTION = "Detecting Changes"
    PRUNING_KNOWLEDGE_GRAPH = "Pruning Knowledge Graph"
    PHYSICAL_NODE_SYNC = "Syncing Physical Nodes"
    MODEL_LINEAGE = "Building Model Lineage"
    SQL_CANONICALIZATION = "Canonicalizing SQL"
    COLUMN_LINEAGE = "Building Column Lineage"
    GRAPH_WRITE = "Populating Knowledge Graph (Lineage)"
    SEMANTIC_VIEWS = "Loading Warehouse Semantic Models"
    PROFILING = "Profiling Physical Tables"
    SEMANTIC_ANALYSIS = "Performing Semantic Analysis"
    SEMANTIC_CLASSIFICATION = "Classifying Columns & Time"
    SEMANTIC_LLM_PASSES = "LLM Analysis (Audit & Grain)"
    SEMANTIC_GRAPH_WRITE = "Populating Knowledge Graph (Semantic Analysis)"
    CLUSTERING = "Understanding Data Relationships"
    COMPLETE = "Complete"


@dataclass
class ProgressUpdate:
    """A progress update event."""

    phase: SyncPhase
    current: int
    total: int
    message: str = ""
    details: str = ""


def _render_progress_details(message: str, details: str) -> str:
    """Render the right-side progress "details" text for Rich.

    Some callers (e.g. `phase_start` / `phase_complete`) populate `message`,
    while the Rich renderer historically only displayed `details`. We render:

    - message + " — " + details, if both are present
    - message, if only message is present
    - details, if only details is present
    - "" otherwise
    """
    message = (message or "").strip()
    details = (details or "").strip()
    if message and details:
        return f"{message} — {details}"
    return message or details or ""


class ProgressCallback(Protocol):
    """Protocol for progress callback handlers."""

    def __call__(self, update: ProgressUpdate) -> None:
        """Handle a progress update."""
        ...


class ProgressTracker:
    """Thread-safe progress tracker that dispatches to registered callbacks.

    This class provides a simple interface for emitting progress updates
    throughout the sync process. If no callback is registered, updates
    are silently ignored (no-op pattern).

    Example:
        >>> def my_callback(update: ProgressUpdate) -> None:
        ...     print(f"{update.phase.value}: {update.current}/{update.total}")
        >>> tracker = ProgressTracker(callback=my_callback)
        >>> tracker.phase_start(SyncPhase.MANIFEST_PARSING, 1)
        >>> tracker.phase_complete(SyncPhase.MANIFEST_PARSING)
    """

    def __init__(self, callback: Optional[ProgressCallback] = None):
        """Initialize the tracker.

        Args:
            callback: Optional callback to receive progress updates.
                     If None, all updates are silently ignored.
        """
        self.callback = callback

    def update(
        self,
        phase: SyncPhase,
        current: int,
        total: int,
        message: str = "",
        details: str = "",
    ) -> None:
        """Emit a progress update.

        Args:
            phase: Current sync phase
            current: Current progress value
            total: Total progress value
            message: Optional status message
            details: Optional detailed information
        """
        if self.callback:
            self.callback(ProgressUpdate(phase, current, total, message, details))

    def phase_start(
        self, phase: SyncPhase, total: int, message: str = ""
    ) -> None:
        """Signal the start of a phase.

        Args:
            phase: Phase being started
            total: Total items to process in this phase
            message: Optional status message
        """
        self.update(phase, 0, total, message)

    def phase_complete(self, phase: SyncPhase, message: str = "") -> None:
        """Signal completion of a phase.

        Args:
            phase: Phase being completed
            message: Optional completion message
        """
        self.update(phase, 1, 1, message or "Complete")


# Type alias for simpler callback signature used by bulk_load
BulkLoadProgressCallback = Callable[[int, int, str], None]

# Human-readable descriptions for semantic analysis passes
PASS_DESCRIPTIONS: dict[str, str] = {
    "relation_analysis": "Extracting tables & aliases...",
    "column_analysis": "Extracting column references...",
    "join_analysis": "Extracting join relationships...",
    "filter_analysis": "Extracting filter predicates...",
    "grouping_analysis": "Analyzing GROUP BY & grain...",
    "time_analysis": "Analyzing time semantics...",
    "window_analysis": "Analyzing window functions...",
    "output_shape_analysis": "Analyzing output shape...",
    "classification": "Classifying columns & time...",
    "semantic_classification": "Classifying semantic roles...",
    "time_classification": "Classifying time columns...",
    "filter_intent": "Analyzing filter business context...",
    "audit_analysis": "Validating analysis...",
    "business_semantics": "Extracting business meaning...",
    "grain_humanization": "Humanizing grain description...",
    "analysis_summary": "Generating analysis summary...",
    "model_domains": "Identifying data domains...",
}


class RichProgressHandler:
    """Rich-based progress display for CLI context.

    This handler renders progress bars using Rich's Progress widget,
    showing each phase as a separate task with completion percentage.

    Example:
        >>> with RichProgressHandler() as handler:
        ...     tracker = ProgressTracker(callback=handler)
        ...     tracker.phase_start(SyncPhase.MANIFEST_PARSING, 1)
        ...     tracker.phase_complete(SyncPhase.MANIFEST_PARSING)
    """

    def __init__(self):
        """Initialize the Rich progress handler."""
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
            TimeElapsedColumn,
        )

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description:<25}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[details]}"),
            TimeElapsedColumn(),
        )
        self._tasks: dict[SyncPhase, TaskID] = {}
        self._current_phase: Optional[SyncPhase] = None

    def __call__(self, update: ProgressUpdate) -> None:
        """Handle a progress update.

        Creates new tasks for new phases and updates existing tasks.
        """
        phase = update.phase
        rendered_details = _render_progress_details(update.message, update.details)

        # Skip COMPLETE phase - it's just a signal
        if phase == SyncPhase.COMPLETE:
            return

        # Create task if this is a new phase
        if phase not in self._tasks:
            task_id = self.progress.add_task(
                phase.value,
                total=update.total or 100,
                details=rendered_details,
            )
            self._tasks[phase] = task_id

        # Update the task
        task_id = self._tasks[phase]
        self.progress.update(
            task_id,
            completed=update.current,
            total=update.total,
            details=rendered_details,
        )

        self._current_phase = phase

    def __enter__(self) -> "RichProgressHandler":
        """Start the progress display."""
        self.progress.start()
        return self

    def __exit__(self, *args) -> None:
        """Stop the progress display."""
        self.progress.stop()

    @property
    def console(self):
        """Access the Rich console for printing messages."""
        return self.progress.console

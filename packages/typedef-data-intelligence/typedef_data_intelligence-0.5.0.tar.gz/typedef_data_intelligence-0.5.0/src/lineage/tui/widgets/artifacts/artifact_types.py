"""Type definitions for artifact widgets.

Contains data classes and message types used across artifact modules.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

from textual.message import Message as TextualMessage
from textual.widgets import Markdown

from lineage.tui.widgets.image import (
    open_file_with_system,
    open_url_in_browser,
)

if TYPE_CHECKING:
    from lineage.tui.widgets.artifacts.viewer import ArtifactViewer


class ExportReportRequest(TextualMessage):
    """Message emitted when user clicks Export HTML button."""

    def __init__(self, report_id: str, artifact_id: str):
        """Initialize export request with report and artifact IDs."""
        super().__init__()
        self.report_id = report_id
        self.artifact_id = artifact_id


class ClickableMarkdown(Markdown):
    """Markdown widget with clickable links that open in browser or system viewer."""

    async def _on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        """Handle link clicks - open files or URLs externally."""
        event.prevent_default()
        url = event.href

        if url.startswith("file://"):
            # File URL - open with system
            path = Path(url.replace("file://", ""))
            self._open_file_path(path)
        elif url.startswith("/"):
            # Absolute path - open with system
            path = Path(url)
            self._open_file_path(path)
        elif url.startswith("http://") or url.startswith("https://"):
            # Web URL - open in browser
            if open_url_in_browser(url):
                self.app.notify("Opened in browser", title="Opened")
            else:
                self.app.notify("Failed to open URL", severity="error")
        elif "://" not in url:
            # No scheme - likely a relative file path or just a filename
            # Try to resolve it as a path
            path = Path(url)
            if not path.is_absolute():
                # Try resolving relative to cwd
                path = Path.cwd() / path
            self._open_file_path(path)
        else:
            # Unknown scheme - try as URL
            if open_url_in_browser(url):
                self.app.notify("Opened in browser", title="Opened")

    def _open_file_path(self, path: Path) -> None:
        """Helper to open a file path with system viewer."""
        if path.exists():
            if open_file_with_system(path):
                self.app.notify(f"Opened {path.name}", title="Opened")
            else:
                self.app.notify("Failed to open file", severity="error")
        else:
            self.app.notify(f"File not found: {path}", severity="error")


@dataclass
class ArtifactData:
    """Stores data for a generated artifact."""

    id: str
    type: str  # 'table', 'chart', 'report', 'activity'
    title: str
    data: Any
    render_func: Callable[["ArtifactViewer", Any], None]
    tool_call_id: Optional[str] = None  # Link to originating tool call

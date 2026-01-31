"""Sync progress TUI for typedef.

This module provides a real-time progress display for the `typedef sync` command.
"""
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Label, ProgressBar, Static

# Path to shared CSS file
STYLES_PATH = Path(__file__).parent / "styles.tcss"


class SyncProgressApp(App):
    """Real-time sync progress display."""

    CSS_PATH = STYLES_PATH

    # Reactive properties for live updates
    current_project = reactive("Initializing...")
    current_message = reactive("Starting sync...")
    current_progress = reactive(0.0)

    def compose(self) -> ComposeResult:
        """Compose the sync progress display."""
        with Vertical(classes="progress-container") as container:
            container.border_title = "Syncing Projects"
            
            yield Label("Syncing dbt projects to graph", classes="progress-title")
            
            yield Static(id="current-project", classes="progress-project")
            yield ProgressBar(id="progress-bar", total=100, show_eta=False)
            yield Static(id="status-message", classes="progress-status")
            yield Static(id="details-message", classes="progress-details")

    def on_mount(self) -> None:
        """Initialize display."""
        self.update_display()

    def watch_current_project(self, value: str) -> None:
        """Update project label when changed."""
        self.update_display()

    def watch_current_message(self, value: str) -> None:
        """Update message when changed."""
        self.update_display()

    def watch_current_progress(self, value: float) -> None:
        """Update progress bar when changed."""
        self.update_display()

    def update_display(self) -> None:
        """Update all display elements."""
        try:
            self.query_one("#current-project", Static).update(
                f"📁 Project: {self.current_project}"
            )
            self.query_one("#progress-bar", ProgressBar).update(
                progress=self.current_progress
            )
            self.query_one("#status-message", Static).update(
                f"Status: {self.current_message}"
            )
        except NoMatches:
            # Widgets might not be mounted yet
            pass

    def update_progress(
        self,
        project: str,
        percent: float,
        message: str,
        details: str = "",
    ) -> None:
        """Update progress from sync operation.
        
        Args:
            project: Current project name
            percent: Progress percentage (0-100)
            message: Status message
            details: Optional detailed message
        """
        self.current_project = project
        self.current_progress = percent
        self.current_message = message
        
        if details:
            try:
                self.query_one("#details-message", Static).update(details)
            except NoMatches:
                pass

    def set_complete(self, message: str = "Sync complete!") -> None:
        """Mark sync as complete."""
        self.current_progress = 100
        self.current_message = message
        try:
            self.query_one("#progress-bar", ProgressBar).update(progress=100)
        except NoMatches:
            pass

    def set_error(self, error_message: str) -> None:
        """Display an error."""
        self.current_message = f"❌ Error: {error_message}"
        try:
            msg_widget = self.query_one("#status-message", Static)
            msg_widget.update(self.current_message)
            msg_widget.styles.color = "#ff4d4f"
        except NoMatches:
            pass


"""Project selector TUI for typedef.

This module provides an interactive project selector for the `typedef chat` command.
"""
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView

# Path to shared CSS file
STYLES_PATH = Path(__file__).parent / "styles.tcss"


class ProjectSelectorScreen(Screen):
    """Project selector with keyboard navigation."""

    CSS_PATH = STYLES_PATH

    def __init__(self, projects: dict, default_project: Optional[str] = None):
        """Initialize project selector screen with available projects."""
        super().__init__()
        self.projects = projects
        self.default_project = default_project
        self.selected_project: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Compose the project selector."""
        with Vertical(classes="selector-container") as container:
            container.border_title = "Select Project"

            yield Label(
                "Choose a project to open",
                classes="selector-description",
            )

            # Build list items first, then pass to ListView constructor
            list_items = []
            for name, config in self.projects.items():
                is_default = name == self.default_project
                default_marker = " [default]" if is_default else ""

                item_content = Vertical(
                    Label(f"📁 {name}{default_marker}", classes="project-name"),
                    Label(f"   Path: {config.get('dbt_path', 'N/A')}", classes="project-path"),
                    Label(
                        f"   Graph: {config.get('graph_name', name)}",
                        classes="project-graph",
                    ),
                )
                list_items.append(ListItem(item_content))

            yield ListView(*list_items)

            yield Label(
                "↑↓ Navigate  |  Enter Select  |  Esc Cancel",
                classes="selector-hint",
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle project selection."""
        # Get the selected project name by index
        project_names = list(self.projects.keys())
        if event.list_view.index is not None and event.list_view.index < len(project_names):
            self.selected_project = project_names[event.list_view.index]
            self.dismiss(self.selected_project)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss(None)


class ProjectSelectorApp(App):
    """Standalone project selector application."""

    def __init__(self, projects: dict, default_project: Optional[str] = None):
        """Initialize standalone project selector application."""
        super().__init__()
        self.projects = projects
        self.default_project = default_project
        self.selected: Optional[str] = None

    def on_mount(self) -> None:
        """Mount the project selector screen."""
        def handle_selection(selected: Optional[str]):
            self.selected = selected
            self.exit()

        self.push_screen(
            ProjectSelectorScreen(self.projects, self.default_project),
            callback=handle_selection,
        )


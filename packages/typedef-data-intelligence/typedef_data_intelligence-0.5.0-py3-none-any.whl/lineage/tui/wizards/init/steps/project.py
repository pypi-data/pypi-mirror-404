"""Project name step for the init wizard."""
from typing import Any

from textual.app import ComposeResult
from textual.widgets import Input, Label, Static

from lineage.tui.wizards.base import WizardStep


class ProjectNameStep(WizardStep):
    """Step 1: Project name."""

    def __init__(self):
        """Initialize project name step."""
        super().__init__(
            title="Project Name",
            description="What would you like to call this project?",
            step_id="project-name",
        )
        self.input: Input

    def get_content(self) -> ComposeResult:
        """Get step content."""
        yield Label("Project name:")
        self.input = Input(
            placeholder="my_analytics",
            id="project-name-input",
        )
        yield self.input
        yield Static(
            "Use letters, numbers, hyphens, and underscores only",
            classes="wizard-hint",
        )

    async def validate(self) -> tuple[bool, str]:
        """Validate project name."""
        value = self.input.value.strip()
        if not value:
            return False, "Project name is required"
        if not value.replace("_", "").replace("-", "").isalnum():
            return False, "Use only letters, numbers, hyphens, and underscores"
        if value.startswith("-") or value.startswith("_"):
            return False, "Project name cannot start with - or _"
        return True, ""

    def get_data(self) -> dict[str, Any]:
        """Get project name data."""
        return {"project_name": self.input.value.strip()}

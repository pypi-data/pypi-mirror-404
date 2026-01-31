"""Integrations step for the init wizard (Linear, Logfire)."""
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static

from lineage.tui.wizards.base import WizardStep


class IntegrationsStep(WizardStep):
    """Step: Optional integrations (Linear ticketing, Logfire telemetry)."""

    def __init__(self):
        """Initialize integrations step."""
        super().__init__(
            title="Integrations (Optional)",
            description="Configure optional integrations for ticketing and telemetry.",
            step_id="integrations",
        )
        self.linear_analyst_key_input: Input
        self.linear_engineer_key_input: Input
        self.linear_team_id_input: Input
        self.logfire_token_input: Input

    def get_content(self) -> ComposeResult:
        """Get step content."""
        yield Button("Load from Environment", id="load-integrations-env-btn", variant="default")
        yield Static(
            "Keys are stored in ~/.typedef/.env. Leave blank to skip.",
            classes="wizard-hint",
        )

        # Linear section
        yield Label("Linear Ticketing", classes="section-header")
        yield Static(
            "Connect Linear to enable the Tickets and Daemon tabs for automated issue management.",
            classes="wizard-hint",
        )

        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("Linear Analyst API key:")
                self.linear_analyst_key_input = Input(
                    placeholder="LINEAR_ANALYST_API_KEY",
                    id="linear-analyst-key-input",
                    password=True,
                )
                yield self.linear_analyst_key_input
            with Vertical(classes="form-field"):
                yield Label("Linear Data Engineer API key:")
                self.linear_engineer_key_input = Input(
                    placeholder="LINEAR_DATA_ENGINEER_API_KEY",
                    id="linear-engineer-key-input",
                    password=True,
                )
                yield self.linear_engineer_key_input

        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("Linear Team ID:")
                self.linear_team_id_input = Input(
                    placeholder="LINEAR_TEAM_ID",
                    id="linear-team-id-input",
                )
                yield self.linear_team_id_input

        # Logfire section
        yield Label("Logfire Telemetry", classes="section-header")
        yield Static(
            "Adding a Logfire token sends telemetry to typedef for product improvement. "
            "All sensitive information is scrubbed before sending.",
            classes="wizard-hint",
        )

        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("Logfire Token:")
                self.logfire_token_input = Input(
                    placeholder="LOGFIRE_TOKEN",
                    id="logfire-token-input",
                    password=True,
                )
                yield self.logfire_token_input

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "load-integrations-env-btn":
            self._load_from_env()

    def _load_from_env(self) -> None:
        """Load keys from environment variables."""
        import os

        from lineage.utils.env import load_env_file

        load_env_file()
        linear_analyst_key = os.getenv("LINEAR_ANALYST_API_KEY")
        if linear_analyst_key:
            self.linear_analyst_key_input.value = linear_analyst_key
        linear_engineer_key = os.getenv("LINEAR_DATA_ENGINEER_API_KEY")
        if linear_engineer_key:
            self.linear_engineer_key_input.value = linear_engineer_key
        linear_team_id = os.getenv("LINEAR_TEAM_ID")
        if linear_team_id:
            self.linear_team_id_input.value = linear_team_id
        logfire_token = os.getenv("LOGFIRE_TOKEN")
        if logfire_token:
            self.logfire_token_input.value = logfire_token

    async def validate(self) -> tuple[bool, str]:
        """Always valid - optional inputs."""
        return True, ""

    def get_data(self) -> dict[str, Any]:
        """Return integration values."""
        return {
            "linear_analyst_api_key": self.linear_analyst_key_input.value.strip(),
            "linear_data_engineer_api_key": self.linear_engineer_key_input.value.strip(),
            "linear_team_id": self.linear_team_id_input.value.strip(),
            "logfire_token": self.logfire_token_input.value.strip(),
        }

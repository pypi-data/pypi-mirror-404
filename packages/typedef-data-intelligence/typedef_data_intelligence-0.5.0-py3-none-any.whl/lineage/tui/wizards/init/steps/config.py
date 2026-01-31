"""Configuration steps for the init wizard (LLM keys, profiles.yml)."""
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static

from lineage.tui.wizards.base import WizardStep
from lineage.tui.wizards.init.helpers import get_profiles_dir


class LlmKeysStep(WizardStep):
    """Step: Optional LLM API keys."""

    def __init__(self):
        """Initialize LLM API key step."""
        super().__init__(
            title="LLM API Keys (Optional)",
            description="Add API keys for OpenAI or Anthropic (optional).",
            step_id="llm-keys",
        )
        self.openai_key_input: Input
        self.anthropic_key_input: Input

    def get_content(self) -> ComposeResult:
        """Get step content."""
        yield Button("Load from Environment", id="load-llm-env-btn", variant="default")
        yield Static(
            "Keys are stored in ~/.typedef/.env. Leave blank to skip.",
            classes="wizard-hint",
        )

        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("OpenAI API key:")
                self.openai_key_input = Input(
                    placeholder="OPENAI_API_KEY",
                    id="openai-key-input",
                    password=True,
                )
                yield self.openai_key_input
            with Vertical(classes="form-field"):
                yield Label("Anthropic API key:")
                self.anthropic_key_input = Input(
                    placeholder="ANTHROPIC_API_KEY",
                    id="anthropic-key-input",
                    password=True,
                )
                yield self.anthropic_key_input

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "load-llm-env-btn":
            self._load_from_env()

    def _load_from_env(self) -> None:
        """Load keys from environment variables."""
        import os

        from lineage.utils.env import load_env_file

        load_env_file()
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_key_input.value = openai_key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_key_input.value = anthropic_key

    async def validate(self) -> tuple[bool, str]:
        """Always valid - optional inputs."""
        return True, ""

    def get_data(self) -> dict[str, Any]:
        """Return API key values."""
        return {
            "openai_api_key": self.openai_key_input.value.strip(),
            "anthropic_api_key": self.anthropic_key_input.value.strip(),
        }


class ProfilesYmlStep(WizardStep):
    """Step 6: Generate profiles.yml preview for dbt project."""

    def __init__(self):
        """Initialize profiles.yml generation step."""
        super().__init__(
            title="Generate profiles.yml",
            description="We'll create a profiles.yml file for your dbt project.",
            step_id="profiles-yml",
        )
        self.preview_content: str = ""
        self.skip_step: bool = False

    def _generate_profiles_yml(self, data: dict[str, Any]) -> str:
        """Generate profiles.yml content from wizard data."""
        import yaml

        profile_name = data.get("profile_name", "dev")
        dbt_target = data.get("dbt_target", "prod")  # Use user-specified target
        account = data.get("snowflake_account", "")
        user = data.get("snowflake_user", "")
        role = data.get("snowflake_role", "")
        warehouse = data.get("snowflake_warehouse", "")
        database = data.get("snowflake_database", "")
        schema = data.get("snowflake_schema", "PUBLIC")
        private_key_path = data.get("snowflake_private_key_path", "")

        profile_config = {
            profile_name: {
                "target": dbt_target,
                "outputs": {
                    dbt_target: {
                        "type": "snowflake",
                        "account": account,
                        "user": user,
                        "role": role,
                        "warehouse": warehouse,
                        "database": database,
                        "schema": schema,
                        "private_key_path": private_key_path,
                        "threads": 8,
                    }
                }
            }
        }

        return yaml.dump(profile_config, default_flow_style=False, sort_keys=False)

    def get_content(self) -> ComposeResult:
        """Get step content."""
        # Check if profiles.yml already exists
        if self.screen and hasattr(self.screen, "wizard_data"):
            needs_generation = self.screen.wizard_data.get("needs_profile_generation", True)
            if not needs_generation:
                self.skip_step = True
                yield Static(
                    "✅ Existing profiles.yml found - will not be overwritten",
                    classes="wizard-hint"
                )
                yield Static(
                    "Press Next to continue to validation checks.",
                    classes="wizard-hint"
                )
                return

            # Generate preview
            self.preview_content = self._generate_profiles_yml(self.screen.wizard_data)

        yield Label("Preview of profiles.yml that will be created:")
        yield Static(self.preview_content, id="profiles-preview", classes="code-preview")

        # Show where file will be written
        project_name = (
            self.screen.wizard_data.get("project_name", "default_project")
            if self.screen and hasattr(self.screen, "wizard_data")
            else "default_project"
        )
        profiles_dir = get_profiles_dir(project_name)

        yield Static(
            f"File will be written to: {profiles_dir}/profiles.yml",
            classes="wizard-hint"
        )
        yield Static(
            "This file will be created when you complete the wizard.",
            classes="wizard-hint"
        )

    async def validate(self) -> tuple[bool, str]:
        """Validate step."""
        if self.skip_step:
            return True, ""

        # Ensure we have generated content
        if not self.preview_content:
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.preview_content = self._generate_profiles_yml(self.screen.wizard_data)

        return True, ""

    def get_data(self) -> dict[str, Any]:
        """Return the profiles.yml content to be written."""
        if self.skip_step:
            return {}
        return {"profiles_yml_content": self.preview_content}

"""Validation and summary steps for the init wizard."""
import subprocess
from pathlib import Path
from typing import Any

from rich.markup import escape as escape_markup
from textual import work
from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.widgets import Label, Static

from lineage.tui.wizards.base import AsyncStepMixin, StepState, WizardStep
from lineage.tui.wizards.init.helpers import (
    TYPEDEF_HOME,
    ensure_dbt_venv,
    focus_button,
    get_adapter_venv_dir,
    get_profiles_dir,
    set_button_disabled,
    strip_ansi_codes,
    upsert_env_file,
)
from lineage.utils.dbt import run_dbt_command
from lineage.utils.snowflake import validate_snowflake_read_access


class PreFlightCheckStep(WizardStep, AsyncStepMixin):
    """Step: Pre-flight checks including profiles.yml generation and dbt docs generate."""

    def __init__(self):
        """Initialize pre-flight check step."""
        super().__init__(
            title="Setup & Validation",
            description="Writing configuration files and validating your setup...",
            step_id="pre-flight",
        )
        self.init_async_state()
        self.dbt_error_output: str = ""  # Store dbt error output for display

    def get_content(self) -> ComposeResult:
        """Get step content."""
        yield Static("1. Ensuring dbt venv...", id="check-venv", classes="wizard-hint")
        yield Static("2. Writing profiles.yml...", id="check-profiles", classes="wizard-hint")
        yield Static("3. Writing .env (optional)...", id="check-env", classes="wizard-hint")
        yield Static("4. Validating Snowflake connection...", id="check-connection", classes="wizard-hint")
        yield Static("5. Checking database access...", id="check-access", classes="wizard-hint")
        yield Static("6. Running dbt docs generate...", id="check-dbt", classes="wizard-hint")
        yield Static("7. Verifying manifest.json...", id="check-manifest", classes="wizard-hint")
        # Error details area (initially empty)
        yield Static("", id="error-details", classes="wizard-hint")

    def on_mount(self) -> None:
        """Run checks when step is mounted."""
        if self.state == StepState.IDLE:
            self.run_checks()

    @work(thread=True)
    def run_checks(self) -> None:
        """Run all setup and validation in background thread."""
        if self.state != StepState.IDLE:
            return

        self.set_state(StepState.WORKING)
        set_button_disabled("next-btn", True, self.app)

        if not self.screen or not hasattr(self.screen, "wizard_data"):
            self.set_state(StepState.FAILED, "Missing wizard data")
            set_button_disabled("next-btn", False, self.app)
            return

        data = self.screen.wizard_data
        dbt_project_root = Path(data.get("dbt_project_root", data.get("dbt_path", "")))

        def update_ui(selector: str, text: str) -> None:
            try:
                self.query_one(selector, Static).update(text)
            except NoMatches:
                pass

        # === Step 1: Ensure dbt venv (shared by adapter) ===
        self.app.call_from_thread(update_ui, "#step-status", "⏳ Ensuring dbt venv...")
        try:
            venv_dir = ensure_dbt_venv(adapter="snowflake")
            self.app.call_from_thread(update_ui, "#check-venv", f"✅ dbt venv ready at {venv_dir}")
        except Exception as e:
            escaped_error = escape_markup(str(e))
            self.app.call_from_thread(update_ui, "#check-venv", f"❌ Failed to setup venv: {escaped_error}")
            self.app.call_from_thread(update_ui, "#step-status", "❌ Failed to setup dbt venv")
            self.set_state(StepState.FAILED, escaped_error)
            set_button_disabled("next-btn", False, self.app)
            return

        # === Step 2: Write profiles.yml if needed ===
        project_name = data.get("project_name", "default_project")
        profiles_dir = get_profiles_dir(project_name)
        self.app.call_from_thread(update_ui, "#step-status", "⏳ Writing profiles.yml...")
        if data.get("needs_profile_generation") and data.get("profiles_yml_content"):
            profile_path = profiles_dir / "profiles.yml"
            try:
                profiles_dir.mkdir(parents=True, exist_ok=True)
                profile_path.write_text(data["profiles_yml_content"])
                self.app.call_from_thread(update_ui, "#check-profiles", "✅ profiles.yml written")
            except Exception as e:
                # Escape error to prevent Rich markup parsing errors
                escaped_error = escape_markup(str(e))
                self.app.call_from_thread(update_ui, "#check-profiles", f"❌ Failed to write profiles.yml: {escaped_error}")
                self.app.call_from_thread(update_ui, "#step-status", "❌ Failed to write profiles.yml")
                self.set_state(StepState.FAILED, escaped_error)
                set_button_disabled("next-btn", False, self.app)
                return
        else:
            self.app.call_from_thread(update_ui, "#check-profiles", "✅ profiles.yml already exists")

        # === Step 3: Write ~/.typedef/.env (optional) ===
        self.app.call_from_thread(update_ui, "#step-status", "⏳ Writing .env...")
        env_updates: dict[str, str] = {
            # Suppress deprecation and user warnings from C extensions and libraries
            "PYTHONWARNINGS": "ignore::DeprecationWarning,ignore::UserWarning",
        }
        openai_key = data.get("openai_api_key", "").strip()
        anthropic_key = data.get("anthropic_api_key", "").strip()
        linear_analyst_key = data.get("linear_analyst_api_key", "").strip()
        linear_engineer_key = data.get("linear_data_engineer_api_key", "").strip()
        linear_team_id = data.get("linear_team_id", "").strip()
        logfire_token = data.get("logfire_token", "").strip()
        if openai_key:
            env_updates["OPENAI_API_KEY"] = openai_key
        if anthropic_key:
            env_updates["ANTHROPIC_API_KEY"] = anthropic_key
        if linear_analyst_key:
            env_updates["LINEAR_ANALYST_API_KEY"] = linear_analyst_key
        if linear_engineer_key:
            env_updates["LINEAR_DATA_ENGINEER_API_KEY"] = linear_engineer_key
        if linear_team_id:
            env_updates["LINEAR_TEAM_ID"] = linear_team_id
        if logfire_token:
            env_updates["LOGFIRE_TOKEN"] = logfire_token

        try:
            if env_updates:
                upsert_env_file(TYPEDEF_HOME / ".env", env_updates)
                self.app.call_from_thread(update_ui, "#check-env", "✅ .env updated")
            else:
                self.app.call_from_thread(update_ui, "#check-env", "✅ .env unchanged")
        except Exception as e:
            escaped_error = escape_markup(str(e))
            self.app.call_from_thread(update_ui, "#check-env", f"❌ Failed to write .env: {escaped_error}")
            self.app.call_from_thread(update_ui, "#step-status", "❌ Failed to write .env")
            self.set_state(StepState.FAILED, escaped_error)
            set_button_disabled("next-btn", False, self.app)
            return

        # === Step 4: Validate Snowflake connection config ===
        self.app.call_from_thread(update_ui, "#step-status", "⏳ Validating Snowflake connection...")
        account = data.get("snowflake_account")
        user = data.get("snowflake_user")
        role = data.get("snowflake_role")
        warehouse = data.get("snowflake_warehouse")
        key_path = data.get("snowflake_private_key_path")
        database = data.get("snowflake_database")
        schema = data.get("snowflake_schema")

        if not all([account, user, role, warehouse, key_path, database]):
            self.app.call_from_thread(update_ui, "#check-connection", "❌ Missing configuration")
            self.app.call_from_thread(update_ui, "#step-status", "❌ Missing Snowflake configuration")
            self.set_state(StepState.FAILED, "Missing Snowflake configuration")
            set_button_disabled("next-btn", False, self.app)
            return

        self.app.call_from_thread(update_ui, "#check-connection", "✅ Connection configuration valid")

        # === Step 5: Check database access (test actual connection) ===
        self.app.call_from_thread(update_ui, "#step-status", "⏳ Checking database access...")
        success, msg, _table = validate_snowflake_read_access(
            account=account,
            user=user,
            role=role,
            warehouse=warehouse,
            private_key_path=key_path,
            database=database,
            schema=schema,
        )

        if success:
            self.app.call_from_thread(update_ui, "#check-access", f"✅ Database access confirmed ({escape_markup(msg)})")
        else:
            # Escape error to prevent Rich markup parsing errors
            escaped_msg = escape_markup(msg)
            self.app.call_from_thread(update_ui, "#check-access", f"❌ Database access failed: {escaped_msg}")
            self.app.call_from_thread(update_ui, "#step-status", "❌ Database access check failed")
            self.set_state(StepState.FAILED, f"Database access failed: {escaped_msg}")
            set_button_disabled("next-btn", False, self.app)
            return

        # === Step 6: Run dbt docs generate if manifest doesn't exist ===
        manifest_path = dbt_project_root / "target" / "manifest.json"
        if not manifest_path.exists():
            self.app.call_from_thread(update_ui, "#step-status", "⏳ Running dbt docs generate (this may take a minute)...")
            try:
                venv_dir = get_adapter_venv_dir("snowflake")
                run_dbt_command(
                    ["docs", "generate"],
                    dbt_project_root,
                    profiles_dir=profiles_dir,
                    venv_dir=venv_dir
                )
                self.app.call_from_thread(update_ui, "#check-dbt", "✅ dbt docs generate complete")
            except subprocess.CalledProcessError as e:
                # Capture error output for display - stderr has the actual error
                error_output = e.stderr or e.stdout or str(e)
                self.dbt_error_output = error_output
                # Strip ANSI codes and show truncated error (dbt output may have ANSI codes)
                error_preview = strip_ansi_codes(error_output.strip().replace("\n", " ")[:200])
                self.app.call_from_thread(update_ui, "#check-dbt", "❌ dbt docs generate failed")
                self.app.call_from_thread(update_ui, "#error-details", error_preview)
                self.app.call_from_thread(update_ui, "#step-status", f"❌ dbt failed: {error_preview[:100]}")
                self.set_state(StepState.FAILED, "dbt docs generate failed")
                set_button_disabled("next-btn", False, self.app)
                return
            except Exception as e:
                # Strip ANSI codes from error (dbt output may contain them)
                error_str = strip_ansi_codes(str(e))
                self.app.call_from_thread(update_ui, "#check-dbt", "❌ dbt docs generate failed")
                self.app.call_from_thread(update_ui, "#error-details", error_str[:200])
                self.app.call_from_thread(update_ui, "#step-status", f"❌ dbt failed: {error_str[:100]}")
                self.set_state(StepState.FAILED, error_str)
                set_button_disabled("next-btn", False, self.app)
                return
        else:
            self.app.call_from_thread(update_ui, "#check-dbt", "✅ manifest.json already exists")

        # === Step 7: Verify manifest.json exists (required for sync) ===
        if manifest_path.exists():
            self.app.call_from_thread(update_ui, "#check-manifest", "✅ manifest.json verified")
        else:
            self.app.call_from_thread(update_ui, "#check-manifest", "❌ manifest.json not found - sync will fail")
            self.app.call_from_thread(update_ui, "#step-status", "❌ Cannot continue without manifest.json")
            self.set_state(StepState.FAILED, "manifest.json not found after dbt docs generate")
            set_button_disabled("next-btn", False, self.app)
            return

        # All checks passed
        self.set_state(StepState.COMPLETED)
        self.app.call_from_thread(update_ui, "#step-status", "✅ All checks passed! Ready to complete setup.")
        set_button_disabled("next-btn", False, self.app)
        focus_button("next-btn", self.app)

    async def validate(self) -> tuple[bool, str]:
        """Validate using state machine."""
        return self.check_async_state()

    def get_data(self) -> dict[str, Any]:
        """Return setup status."""
        return {"setup_completed": self.state == StepState.COMPLETED}


class SummaryStep(WizardStep):
    """Final step: Summary of all configuration before completing setup."""

    def __init__(self):
        """Initialize summary step."""
        super().__init__(
            title="Setup Summary",
            description="Review your configuration before completing setup.",
            step_id="summary",
        )

    def get_content(self) -> ComposeResult:
        """Get step content with summary sections."""
        # Project Configuration
        yield Label("Project Configuration", classes="section-header")
        yield Static(id="summary-project")

        # dbt Project
        yield Label("dbt Project", classes="section-header")
        yield Static(id="summary-dbt")

        # Snowflake Connection
        yield Label("Snowflake Connection", classes="section-header")
        yield Static(id="summary-snowflake")

        # Files to Create
        yield Label("Files to Create", classes="section-header")
        yield Static(id="summary-files")

    def on_mount(self) -> None:
        """Populate summary from wizard data when mounted."""
        if not self.screen or not hasattr(self.screen, "wizard_data"):
            return

        data = self.screen.wizard_data

        # Project info
        project_name = data.get("project_name", "N/A")
        try:
            self.query_one("#summary-project", Static).update(
                f"  Name: {project_name}"
            )
        except NoMatches:
            pass

        # dbt info
        dbt_path = data.get("dbt_project_root", data.get("dbt_path", "N/A"))
        profile_name = data.get("profile_name", "N/A")
        is_git_clone = data.get("is_git_clone", False)
        source_type = "Git clone" if is_git_clone else "Local path"
        try:
            self.query_one("#summary-dbt", Static).update(
                f"  Path: {dbt_path}\n"
                f"  Profile: {profile_name}\n"
                f"  Source: {source_type}"
            )
        except NoMatches:
            pass

        # Snowflake info
        account = data.get("snowflake_account", "N/A")
        user = data.get("snowflake_user", "N/A")
        role = data.get("snowflake_role", "N/A")
        warehouse = data.get("snowflake_warehouse", "N/A")
        database = data.get("snowflake_database", "N/A")
        try:
            self.query_one("#summary-snowflake", Static).update(
                f"  Account: {account}\n"
                f"  User: {user}\n"
                f"  Role: {role}\n"
                f"  Warehouse: {warehouse}\n"
                f"  Database: {database}"
            )
        except NoMatches:
            pass

        # Files that will be created
        files = []
        needs_profile = data.get("needs_profile_generation", True)
        if needs_profile:
            profiles_dir = get_profiles_dir(project_name)
            files.append(f"  - {profiles_dir}/profiles.yml")
        files.append("  - ~/.typedef/venvs/dbt-snowflake/")
        files.append("  - ~/.typedef/.env")
        files.append(f"  - ~/.typedef/projects/{project_name}/config.yml")
        try:
            self.query_one("#summary-files", Static).update("\n".join(files))
        except NoMatches:
            pass

    async def validate(self) -> tuple[bool, str]:
        """Summary step is always valid - just for review."""
        return True, ""

    def get_data(self) -> dict[str, Any]:
        """No additional data to return."""
        return {}

"""Snowflake connection steps for the init wizard."""
from pathlib import Path
from typing import Any

from rich.markup import escape as escape_markup
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.widgets import Button, Input, Label, Select, SelectionList, Static
from textual.widgets.selection_list import Selection

from lineage.tui.wizards.base import AsyncStepMixin, StepState, WizardStep
from lineage.tui.wizards.init.helpers import (
    focus_button,
    get_dbt_profile_name,
    set_button_disabled,
)
from lineage.utils.snowflake import (
    list_snowflake_databases,
)


class SnowflakeConnectionStep(WizardStep, AsyncStepMixin):
    """Step 3: Snowflake connection configuration with async validation."""

    def __init__(self):
        """Initialize Snowflake connection step."""
        super().__init__(
            title="Snowflake Connection",
            description="Configure your Snowflake connection details.",
            step_id="snowflake-connection",
        )
        self.init_async_state()  # Initialize AsyncStepMixin state
        self.account_input: Input
        self.user_input: Input
        self.role_input: Input
        self.warehouse_input: Input
        self.key_path_input: Input
        self.schema_input: Input
        self.profile_name_input: Input
        self.env_vars_input: Input
        self.db_list: list[str] = []
        self.required_profile_name: str | None = None  # From dbt_project.yml

    def get_content(self) -> ComposeResult:
        """Get step content with 2-column layout for paired fields."""
        # Add environment loading button
        yield Button("Load from Environment", id="load-env-btn", variant="default")

        # Determine profile name from dbt_project.yml
        if self.screen and hasattr(self.screen, "wizard_data"):
            # Use dbt_project_root if available (for subprojects), otherwise dbt_path
            dbt_path = Path(self.screen.wizard_data.get(
                "dbt_project_root",
                self.screen.wizard_data.get("dbt_path", "")
            ))
            self.required_profile_name = get_dbt_profile_name(dbt_path)

        # Check if we need to generate profile
        if self.screen and hasattr(self.screen, "wizard_data"):
            if self.screen.wizard_data.get("needs_profile_generation"):
                if self.required_profile_name:
                    yield Label(
                        f"We'll generate profiles.yml with profile '{self.required_profile_name}' (from dbt_project.yml)",
                        classes="wizard-hint"
                    )
                else:
                    yield Label("We'll use these details to generate your profiles.yml", classes="wizard-hint")

        # Row 1: Account + User (2-column)
        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("Account (e.g., abc123.us-west-2):")
                self.account_input = Input(
                    placeholder="abc123.us-west-2",
                    id="snowflake-account-input",
                )
                yield self.account_input
            with Vertical(classes="form-field"):
                yield Label("User:")
                self.user_input = Input(placeholder="username", id="snowflake-user-input")
                yield self.user_input

        # Row 2: Role + Warehouse (2-column)
        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("Role:")
                self.role_input = Input(placeholder="ANALYST", value="ANALYST", id="snowflake-role-input")
                yield self.role_input
            with Vertical(classes="form-field"):
                yield Label("Warehouse:")
                self.warehouse_input = Input(placeholder="COMPUTE_WH", value="COMPUTE_WH", id="snowflake-warehouse-input")
                yield self.warehouse_input

        # Row 3: Private key path + dbt target environment (2-column)
        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("Private key path:")
                default_key = str(Path.home() / ".ssh" / "snowflake_rsa_key.p8")
                self.key_path_input = Input(
                    placeholder=default_key,
                    value=default_key,
                    id="snowflake-key-input",
                )
                yield self.key_path_input
            with Vertical(classes="form-field"):
                yield Label("dbt target environment:")
                self.dbt_target_input = Input(
                    placeholder="prod",
                    value="prod",
                    id="dbt-target-input",
                )
                yield self.dbt_target_input

        # Row 4: Profile name + Env vars (2-column)
        with Horizontal(classes="form-row"):
            with Vertical(classes="form-field"):
                yield Label("Profile name:")
                default_profile = self.required_profile_name or "dev"
                self.profile_name_input = Input(
                    placeholder=default_profile,
                    value=default_profile,
                    id="profile-name-input",
                    disabled=bool(self.required_profile_name),
                )
                yield self.profile_name_input
            with Vertical(classes="form-field"):
                yield Label("Env vars (key=val,...):")
                self.env_vars_input = Input(
                    placeholder="DBT_ENV=prod",
                    id="env-vars-input",
                )
                yield self.env_vars_input


        # Check if profile exists
        has_profile = False
        if self.screen and hasattr(self.screen, "wizard_data"):
            has_profile = not self.screen.wizard_data.get("needs_profile_generation", True)

        if has_profile:
            yield Static("Existing profiles.yml found - will not be overwritten", classes="wizard-hint")
        elif self.required_profile_name:
            yield Static(f"Profile name '{self.required_profile_name}' is required by dbt_project.yml", classes="wizard-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "load-env-btn":
            self._load_from_env()

    def _load_from_env(self):
        """Load credentials from environment variables."""
        import os

        from lineage.utils.env import load_env_file

        # Ensure environment is loaded
        load_env_file()

        loaded_count = 0

        # Account
        account = os.getenv("SNOWFLAKE_ACCOUNT")
        if account:
            self.account_input.value = account
            loaded_count += 1

        # User
        user = os.getenv("SNOWFLAKE_USER")
        if user:
            self.user_input.value = user
            loaded_count += 1

        # Role
        role = os.getenv("SNOWFLAKE_ROLE")
        if role:
            self.role_input.value = role
            loaded_count += 1

        # Warehouse
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        if warehouse:
            self.warehouse_input.value = warehouse
            loaded_count += 1

        # Key path
        key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
        if key_path:
            self.key_path_input.value = key_path
            loaded_count += 1

        # dbt target (optional - check DBT_TARGET env var)
        dbt_target = os.getenv("DBT_TARGET")
        if dbt_target:
            self.dbt_target_input.value = dbt_target
            loaded_count += 1


        try:
            status = self.query_one("#step-status", Static)
            if loaded_count > 0:
                status.update(f"✅ Loaded {loaded_count} values from environment")
            else:
                status.update("⚠ No SNOWFLAKE_* variables found in environment")
        except NoMatches:
            pass

    def _on_state_changed(self) -> None:
        """Update UI when state changes (called on main thread)."""
        try:
            status = self.query_one("#step-status", Static)
            if self.state == StepState.VALIDATING:
                status.update("⏳ Testing connection and listing databases...")
            elif self.state == StepState.VALID:
                status.update(f"✅ Connection successful! Found {len(self.db_list)} databases.")
            elif self.state == StepState.INVALID:
                status.update(f"❌ {self._error_message}")
        except NoMatches:
            pass

    @work(thread=True)
    def _validate_connection(self) -> None:
        """Background worker to test Snowflake connection."""
        self.set_state(StepState.VALIDATING)

        # Disable Next button while validating
        set_button_disabled("next-btn", True, self.app)

        # Read credentials (safe to read from worker thread)
        account = self.account_input.value.strip()
        user = self.user_input.value.strip()
        role = self.role_input.value.strip()
        warehouse = self.warehouse_input.value.strip()
        key_path = self.key_path_input.value.strip()

        try:
            self.db_list = list_snowflake_databases(
                account=account,
                user=user,
                role=role,
                warehouse=warehouse,
                private_key_path=key_path,
            )

            # Store db list in wizard data for next step
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.screen.wizard_data["available_databases"] = self.db_list

            self.set_state(StepState.VALID)

            # Re-enable and focus Next button
            set_button_disabled("next-btn", False, self.app)
            focus_button("next-btn", self.app)

        except Exception as e:
            # Escape error to prevent Rich markup parsing errors
            self.set_state(StepState.INVALID, f"Connection failed: {escape_markup(str(e))}")
            # Re-enable Next so user can retry after fixing
            set_button_disabled("next-btn", False, self.app)

    async def validate(self) -> tuple[bool, str]:
        """Validate inputs and test connection using state machine."""
        # First check required fields (synchronous validation)
        account = self.account_input.value.strip()
        user = self.user_input.value.strip()
        role = self.role_input.value.strip()
        warehouse = self.warehouse_input.value.strip()
        key_path = self.key_path_input.value.strip()

        if not all([account, user, role, warehouse, key_path]):
            return False, "All fields are required"

        if not Path(key_path).expanduser().exists():
            return False, f"Private key file not found: {key_path}"

        # State machine for async connection test
        if self.state == StepState.IDLE:
            # Start background validation
            self._validate_connection()
            return False, ""  # Signal "in progress" - no error message

        # Check async state
        return self.check_async_state()

    def get_data(self) -> dict[str, Any]:
        """Get connection data."""
        # Parse env vars from comma-separated key=value format
        env_vars = {}
        env_vars_str = self.env_vars_input.value.strip()
        if env_vars_str:
            for pair in env_vars_str.split(","):
                pair = pair.strip()
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key:  # Only add if key is non-empty
                        env_vars[key] = value

        # Use required profile name if set (from dbt_project.yml), otherwise user input
        profile_name = self.required_profile_name or self.profile_name_input.value.strip() or "dev"

        return {
            "snowflake_account": self.account_input.value.strip(),
            "snowflake_user": self.user_input.value.strip(),
            "snowflake_role": self.role_input.value.strip(),
            "snowflake_warehouse": self.warehouse_input.value.strip(),
            "snowflake_private_key_path": self.key_path_input.value.strip(),
            "dbt_target": self.dbt_target_input.value.strip() or "prod",
            "profile_name": profile_name,
            "project_env_vars": env_vars,
        }


class DatabaseSelectionStep(WizardStep):
    """Step 5: Database and schema selection."""

    MANUAL_SCHEMA_VALUE = "__MANUAL__"

    def __init__(self):
        """Initialize database selection step."""
        super().__init__(
            title="Select Database & Schema",
            description="Select your default database and schema.",
            step_id="database-selection",
        )
        self.default_db_select: Select
        self.schema_select: Select
        self.manual_schema_input: Input
        self.manual_schema_label: Label
        self.additional_db_select: SelectionList
        self.additional_db_filter_input: Input
        self.manual_db_input: Input
        self.skip_mode = False
        self.available_schemas: list[str] = []
        self.schemas_loaded = False
        self.all_databases: list[str] = []

    def get_content(self) -> ComposeResult:
        """Get step content."""
        # If we have databases from previous step, show selection
        # Otherwise show manual input
        self.skip_mode = True
        if self.screen and hasattr(self.screen, "wizard_data"):
            available_dbs = self.screen.wizard_data.get("available_databases", [])
            if available_dbs:
                self.skip_mode = False
                self.all_databases = list(available_dbs)

                yield Label("Default Database (Required):")
                self.default_db_select = Select(
                    options=[(db, db) for db in available_dbs],
                    prompt="Select a default database",
                    id="default-db-select",
                )
                yield self.default_db_select

                yield Label("Default Schema:")
                # Start with just manual entry option until schemas are loaded
                self.schema_select = Select(
                    options=[("Enter manually", self.MANUAL_SCHEMA_VALUE)],
                    prompt="Select database first...",
                    id="schema-select",
                    disabled=True,
                )
                yield self.schema_select

                self.manual_schema_label = Label("Or enter schema manually:")
                self.manual_schema_label.display = False
                yield self.manual_schema_label
                self.manual_schema_input = Input(
                    placeholder="PUBLIC",
                    value="PUBLIC",
                    id="manual-schema-input",
                )
                self.manual_schema_input.display = False
                yield self.manual_schema_input

                yield Label("Additional Databases (Optional):")
                self.additional_db_filter_input = Input(
                    placeholder="Filter additional databases...",
                    id="additional-db-filter-input",
                )
                yield self.additional_db_filter_input
                self.additional_db_select = SelectionList(
                    *[Selection(db, db) for db in available_dbs],
                    id="additional-db-select",
                )
                yield self.additional_db_select
                return

        # Fallback for manual entry or failed connection
        yield Label(
            "⚠ Could not list databases from Snowflake. Entering manual mode.",
            classes="warning-label",
        )
        yield Label("")  # Spacer
        yield Label("Default Database:")
        self.manual_db_input = Input(
            placeholder="DATABASE_NAME",
            id="manual-db-input",
        )
        yield self.manual_db_input

        yield Label("Default Schema:")
        self.manual_schema_input = Input(
            placeholder="PUBLIC",
            value="PUBLIC",
            id="manual-schema-input",
        )
        yield self.manual_schema_input

        yield Static(
            "Could not fetch database list. Enter values manually.",
            classes="wizard-hint",
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes - load schemas when database is selected."""
        if event.select.id == "default-db-select" and event.value:
            # Load schemas for the selected database
            self._load_schemas(str(event.value))
        elif event.select.id == "schema-select":
            # If user selected manual entry, focus the input
            if event.value == self.MANUAL_SCHEMA_VALUE:
                self.manual_schema_label.display = True
                self.manual_schema_input.display = True
                self.manual_schema_input.focus()
            else:
                self.manual_schema_label.display = False
                self.manual_schema_input.display = False

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input for additional databases."""
        if event.input.id == "additional-db-filter-input":
            self._update_additional_db_options(event.value)

    def _update_additional_db_options(self, query: str) -> None:
        """Filter additional databases list based on input."""
        if not hasattr(self, "additional_db_select"):
            return
        selected = set(self.additional_db_select.selected)
        filtered = self._filter_additional_databases(query, selected)
        options = [Selection(db, db, initial_state=db in selected) for db in filtered]
        self.additional_db_select.set_options(options)

    def _filter_additional_databases(self, query: str, selected: set[str]) -> list[str]:
        """Return databases matching query, preserving selected items."""
        if not query:
            return list(self.all_databases)
        needle = query.strip().lower()
        matches = [db for db in self.all_databases if needle in db.lower()]
        for db in selected:
            if db in self.all_databases and db not in matches:
                matches.append(db)
        return matches

    @work(thread=True)
    def _load_schemas(self, database: str) -> None:
        """Load schemas for the selected database in background."""
        if not self.screen or not hasattr(self.screen, "wizard_data"):
            return

        data = self.screen.wizard_data

        def update_status(text: str) -> None:
            try:
                self.query_one("#step-status", Static).update(text)
            except NoMatches:
                pass

        self.app.call_from_thread(update_status, f"⏳ Loading schemas for {database}...")

        try:
            from lineage.utils.snowflake import list_snowflake_schemas

            schemas = list_snowflake_schemas(
                account=data.get("snowflake_account", ""),
                user=data.get("snowflake_user", ""),
                role=data.get("snowflake_role", ""),
                warehouse=data.get("snowflake_warehouse", ""),
                private_key_path=data.get("snowflake_private_key_path", ""),
                database=database,
            )

            self.available_schemas = schemas
            self.schemas_loaded = True

            # Update the schema select dropdown
            def update_schema_select() -> None:
                try:
                    options = [(s, s) for s in schemas]
                    options.append(("Enter manually", self.MANUAL_SCHEMA_VALUE))
                    self.schema_select.set_options(options)
                    self.schema_select.disabled = False
                    # Pre-select PUBLIC if available
                    if "PUBLIC" in schemas:
                        self.schema_select.value = "PUBLIC"
                except AttributeError:
                    # Widget may not be initialized in skip mode
                    pass

            self.app.call_from_thread(update_schema_select)
            self.app.call_from_thread(update_status, f"✅ Found {len(schemas)} schemas")

        except Exception as e:
            # Escape error to prevent Rich markup parsing errors
            self.app.call_from_thread(update_status, f"⚠ Could not load schemas: {escape_markup(str(e))}")
            # Keep manual input as fallback

    async def validate(self) -> tuple[bool, str]:
        """Validate selection."""
        if self.skip_mode:
            if not self.manual_db_input.value.strip():
                return False, "Database name is required"
            if not self.manual_schema_input.value.strip():
                return False, "Schema name is required"
            return True, ""

        # Check for Select.BLANK (NoSelection) - it's truthy but not a valid selection
        if not self.default_db_select.value or self.default_db_select.value == Select.BLANK:
            return False, "Please select a default database"

        # Check schema - either from dropdown or manual input
        schema_from_select = self.schema_select.value
        schema_from_input = self.manual_schema_input.value.strip()

        # Need manual input if user selected manual entry, or if nothing is selected (BLANK/None)
        needs_manual = (
            schema_from_select == self.MANUAL_SCHEMA_VALUE
            or schema_from_select is None
            or schema_from_select == Select.BLANK
        )
        if needs_manual and not schema_from_input:
            return False, "Please enter a schema name"

        return True, ""

    def get_data(self) -> dict[str, Any]:
        """Get database and schema selection data."""
        if self.skip_mode:
            db = self.manual_db_input.value.strip()
            schema = self.manual_schema_input.value.strip() or "PUBLIC"
            return {
                "snowflake_database": db,
                "snowflake_schema": schema,
                "allowed_databases": [db],
                "allowed_schemas": [],
            }

        default_db = self.default_db_select.value
        additional_dbs = list(self.additional_db_select.selected)

        # Handle Select.BLANK (NoSelection) - convert to empty string for safety
        if default_db == Select.BLANK:
            default_db = ""

        # Get schema - prefer dropdown selection, fall back to manual input
        schema_from_select = self.schema_select.value
        if schema_from_select and schema_from_select != self.MANUAL_SCHEMA_VALUE and schema_from_select != Select.BLANK:
            schema = schema_from_select
        else:
            schema = self.manual_schema_input.value.strip() or "PUBLIC"

        # Combine and deduplicate databases, filtering out empty values
        all_dbs_raw = [default_db] + additional_dbs
        all_dbs = sorted([db for db in set(all_dbs_raw) if db])

        return {
            "snowflake_database": default_db,
            "snowflake_schema": schema,
            "allowed_databases": all_dbs,
            "allowed_schemas": [],
        }

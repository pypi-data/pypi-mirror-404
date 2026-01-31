"""dbt project source steps for the init wizard."""
import threading
from pathlib import Path
from typing import Any, Optional

from textual import work
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, LoadingIndicator, Select, Static

from lineage.tui.wizards.base import WizardStep
from lineage.tui.wizards.init.helpers import (
    create_spinner_toggle,
    create_ui_updater,
    find_dbt_projects,
    get_profiles_dir,
    run_dbt_deps,
    strip_ansi_codes,
)
from lineage.utils.git import clone_repo, is_valid_git_url


class DbtPathStep(WizardStep):
    """Step 2: dbt project path or git repository."""

    SOURCE_GIT = "git"
    SOURCE_LOCAL = "local"
    DEFAULT_GIT_PLACEHOLDER = "https://github.com/org/repo.git"

    def __init__(self):
        """Initialize dbt path step."""
        super().__init__(
            title="dbt Project Location",
            description="Choose a Git URL or an existing local dbt project.",
            step_id="dbt-path",
        )
        self.input: Input
        self.source_select: Select
        self.source_label: Label
        self.source_hint: Static
        self.is_git_url: bool = False
        self.was_git_clone: bool = False  # Persists after input is updated to local path
        self.project_name: str = ""
        self.work_complete: bool = False
        self.work_in_progress: bool = False
        self.work_error: Optional[str] = None
        self.work_mode: Optional[str] = None
        self.work_target: Optional[str] = None
        self._work_lock = threading.Lock()  # Protects work_in_progress flag
        self.default_local_path = str(Path.cwd())

    def get_content(self) -> ComposeResult:
        """Get step content."""
        yield Label("Source type:")
        self.source_select = Select(
            options=[
                ("Git URL", self.SOURCE_GIT),
                ("Existing Project (Local Path)", self.SOURCE_LOCAL),
            ],
            value=self.SOURCE_GIT,
            id="dbt-source-select",
        )
        yield self.source_select

        self.source_label = Label("Git repository URL:", id="dbt-source-label")
        yield self.source_label

        # Try to default to current directory
        self.input = Input(
            placeholder=self.DEFAULT_GIT_PLACEHOLDER,
            value="",
            id="dbt-path-input",
        )
        yield self.input

        self.source_hint = Static(
            "Git URL: We'll clone into ~/.typedef/projects/<project_name> and run dbt deps.",
            id="dbt-source-hint",
            classes="wizard-hint",
        )
        yield self.source_hint

        yield Static(id="clone-status", classes="wizard-hint")

        spinner = LoadingIndicator(id="clone-spinner")
        spinner.display = False
        yield spinner

        # Output display for dbt commands
        yield Static(id="dbt-output", classes="wizard-hint")

    async def validate(self) -> tuple[bool, str]:
        """Validate dbt path or git URL."""
        value = self.input.value.strip()
        mode = self._get_selected_source()
        if not value:
            if mode == self.SOURCE_GIT:
                return False, "Git URL is required"
            return False, "Path is required"

        # Update project name from wizard data
        if self.screen and hasattr(self.screen, "wizard_data"):
            self.project_name = self.screen.wizard_data.get("project_name", "default_project")

        if mode == self.SOURCE_GIT:
            clone_dir = self._get_clone_dir()
            clone_dir_str = str(clone_dir)
            is_clone_path = value == clone_dir_str
            if self.work_complete and not self._work_matches(mode, value) and not is_clone_path:
                self._reset_work_state()
            if self.work_error and not self._work_matches(mode, value) and not is_clone_path:
                self.work_error = None

            if not is_valid_git_url(value):
                if self.work_complete and is_clone_path and self.was_git_clone:
                    return True, ""
                return False, "Enter a valid Git URL"

            self.is_git_url = True
            # Remember this was a git clone (persists after input is updated to local path)
            self.was_git_clone = True

            # Git URL path - need to clone and run dbt
            if self.work_error:
                return False, self.work_error

            if not self.work_complete:
                # Start the work if not already in progress
                if not self.work_in_progress:
                    self.run_git_and_dbt_work(value)
                # Work is in progress - button is disabled, just return True
                # (button will be re-enabled when work completes)
                return False, ""

            # Work is complete
            return True, ""
        else:
            path = Path(value).expanduser().resolve()
            target_value = str(path)
            if self.work_complete and not self._work_matches(mode, target_value):
                self._reset_work_state()
            if self.work_error and not self._work_matches(mode, target_value):
                self.work_error = None

            self.is_git_url = False
            self.was_git_clone = False

            # Local path validation (synchronous, fast)
            if not path.exists():
                return False, f"Path does not exist: {path}"
            if not path.is_dir():
                return False, f"Path is not a directory: {path}"

            # Check if dbt_project.yml exists at root
            has_root_project = (path / "dbt_project.yml").exists()

            if not has_root_project:
                # Check for subprojects (monorepo case)
                subprojects = find_dbt_projects(path, max_depth=3)
                if not subprojects:
                    return False, "No dbt_project.yml found in this directory or subdirectories"
                # Store detected subprojects for next step
                if self.screen and hasattr(self.screen, "wizard_data"):
                    self.screen.wizard_data["detected_subprojects"] = [str(p) for p in subprojects]

            # Check for profiles.yml (stored outside repo)
            profiles_dir = get_profiles_dir(self.project_name)
            has_profile = (profiles_dir / "profiles.yml").exists()
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.screen.wizard_data["needs_profile_generation"] = not has_profile

            if not has_root_project:
                return True, ""

            if self.work_error:
                return False, self.work_error

            if not self.work_complete:
                if not self.work_in_progress:
                    self.run_local_dbt_work(path)
                return False, ""

            return True, ""

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle source type changes."""
        if event.select.id == "dbt-source-select":
            self._update_source_ui(str(event.value))
            self._reset_work_state()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes to reset work state."""
        if event.input.id == "dbt-path-input" and not self.work_in_progress:
            self._reset_work_state()

    def _get_selected_source(self) -> str:
        """Get selected source type with fallback."""
        if hasattr(self, "source_select") and self.source_select.value and self.source_select.value != Select.BLANK:
            return str(self.source_select.value)
        return self.SOURCE_GIT

    def _update_source_ui(self, mode: str) -> None:
        """Update label, placeholder, and hint based on source type."""
        if mode == self.SOURCE_LOCAL:
            self.source_label.update("Existing project path:")
            if self.input.value.strip() in ("", self.DEFAULT_GIT_PLACEHOLDER):
                self.input.value = self.default_local_path
            self.input.placeholder = self.default_local_path
            self.source_hint.update(
                "Existing project path: Use a local dbt project directory. "
                "No git clone will occur. We'll run dbt deps here."
            )
        else:
            self.source_label.update("Git repository URL:")
            if self.input.value.strip() == self.default_local_path:
                self.input.value = ""
            self.input.placeholder = self.DEFAULT_GIT_PLACEHOLDER
            self.source_hint.update(
                "Git URL: We'll clone into ~/.typedef/projects/<project_name> and run dbt deps."
            )

    def _reset_work_state(self) -> None:
        """Reset background work state."""
        self.work_complete = False
        self.work_in_progress = False
        self.work_error = None
        self.work_mode = None
        self.work_target = None
        try:
            self.query_one("#clone-status", Static).update("")
            self.query_one("#dbt-output", Static).update("")
        except Exception: #nosec B110
            # UI update errors are non-fatal; widgets may not be mounted yet.
            pass

    def _work_matches(self, mode: str, target: str) -> bool:
        """Check whether work state matches the current input."""
        return self.work_mode == mode and self.work_target == target

    def _get_clone_dir(self) -> Path:
        """Get the default clone directory for git sources."""
        return Path.home() / ".typedef" / "projects" / self.project_name

    @work(thread=True)
    def run_git_and_dbt_work(self, git_url: str) -> None:
        """Clone repo and run dbt commands in background thread."""
        # Use lock to prevent race condition when clicking rapidly
        with self._work_lock:
            if self.work_in_progress or self.work_complete:
                return
            self.work_in_progress = True
            self.work_error = None
            self.work_mode = self.SOURCE_GIT
            self.work_target = git_url

        # Create UI helpers
        update_ui = create_ui_updater(self)
        show_spinner = create_spinner_toggle(self, "clone-spinner")

        # Disable Next button while working
        if self.screen:
            self.app.call_from_thread(
                lambda: setattr(self.screen.query_one("#next-btn", Button), "disabled", True)
            )

        # Show spinner and update status
        self.app.call_from_thread(show_spinner, True)
        clone_dir = Path.home() / ".typedef" / "projects" / self.project_name
        self.app.call_from_thread(
            update_ui,
            "#clone-status",
            f"⏳ Cloning {git_url} to {clone_dir}..."
        )

        try:
            # Clone repository (or use existing)
            if clone_dir.exists() and any(clone_dir.iterdir()):
                # Directory exists with contents - check if it's a valid project or monorepo
                has_root_project = (clone_dir / "dbt_project.yml").exists()
                has_subprojects = bool(find_dbt_projects(clone_dir, max_depth=3))

                if not has_root_project and not has_subprojects:
                    self.work_error = f"Directory {clone_dir} exists but contains no dbt projects"
                    self.work_in_progress = False
                    self.app.call_from_thread(show_spinner, False)
                    self.app.call_from_thread(update_ui, "#clone-status", f"❌ {self.work_error}")
                    return
                # Already exists and valid - skip clone
                self.app.call_from_thread(update_ui, "#clone-status", f"✅ Using existing clone at {clone_dir}")
            else:
                # Clone fresh
                clone_repo(git_url, clone_dir)
                self.app.call_from_thread(update_ui, "#clone-status", f"✅ Cloned to {clone_dir}")

            # Update input to local path
            self.app.call_from_thread(lambda: setattr(self.input, "value", str(clone_dir)))

            # Check for profiles.yml (stored outside repo)
            profiles_dir = get_profiles_dir(self.project_name)
            has_profile = (profiles_dir / "profiles.yml").exists()
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.screen.wizard_data["needs_profile_generation"] = not has_profile

            # Check if this is a monorepo (no dbt_project.yml at root)
            has_root_project = (clone_dir / "dbt_project.yml").exists()

            if not has_root_project:
                # Monorepo - scan for subprojects
                subprojects = find_dbt_projects(clone_dir, max_depth=3)
                if subprojects:
                    self.app.call_from_thread(
                        update_ui,
                        "#clone-status",
                        f"✅ Clone complete. Found {len(subprojects)} dbt project(s) - select one in next step."
                    )
                    # Store subprojects for next step
                    if self.screen and hasattr(self.screen, "wizard_data"):
                        self.screen.wizard_data["detected_subprojects"] = [str(p) for p in subprojects]
                    # Skip dbt commands - will be run after subproject selection
                else:
                    self.work_error = "No dbt_project.yml found in cloned repository"
                    self.work_in_progress = False
                    self.app.call_from_thread(show_spinner, False)
                    self.app.call_from_thread(update_ui, "#clone-status", f"❌ {self.work_error}")
                    return
            else:
                # Single project at root - run dbt deps only (docs generate needs profile)
                run_dbt_deps(
                    clone_dir, self.app, update_ui,
                    status_selector="#clone-status",
                    output_selector="#dbt-output"
                )

            # Mark work as complete
            self.work_complete = True
            self.work_in_progress = False

            # Hide spinner and re-enable Next button
            self.app.call_from_thread(show_spinner, False)
            if self.screen:
                def enable_next():
                    btn = self.screen.query_one("#next-btn", Button)
                    btn.disabled = False
                    btn.focus()
                self.app.call_from_thread(enable_next)

        except Exception as e:
            # Strip ANSI codes from error message (command output may contain them)
            self.work_error = f"Clone failed: {strip_ansi_codes(str(e))}"
            self.work_in_progress = False
            self.work_complete = False
            self.app.call_from_thread(show_spinner, False)
            self.app.call_from_thread(update_ui, "#clone-status", f"❌ {self.work_error}")
            # Re-enable Next so user can fix and retry
            if self.screen:
                self.app.call_from_thread(
                    lambda: setattr(self.screen.query_one("#next-btn", Button), "disabled", False)
                )

    @work(thread=True)
    def run_local_dbt_work(self, project_path: Path) -> None:
        """Run dbt deps for a local project in background thread."""
        with self._work_lock:
            if self.work_in_progress or self.work_complete:
                return
            self.work_in_progress = True
            self.work_error = None
            self.work_mode = self.SOURCE_LOCAL
            self.work_target = str(project_path)

        update_ui = create_ui_updater(self)
        show_spinner = create_spinner_toggle(self, "clone-spinner")

        if self.screen:
            self.app.call_from_thread(
                lambda: setattr(self.screen.query_one("#next-btn", Button), "disabled", True)
            )

        self.app.call_from_thread(show_spinner, True)
        self.app.call_from_thread(
            update_ui,
            "#clone-status",
            f"⏳ Running dbt deps in {project_path}..."
        )

        try:
            run_dbt_deps(
                project_path,
                self.app,
                update_ui,
                status_selector="#clone-status",
                output_selector="#dbt-output",
            )
            self.work_complete = True
            self.work_in_progress = False

            self.app.call_from_thread(show_spinner, False)
            if self.screen:
                def enable_next():
                    btn = self.screen.query_one("#next-btn", Button)
                    btn.disabled = False
                    btn.focus()
                self.app.call_from_thread(enable_next)
        except Exception as e:
            self.work_error = f"dbt deps failed: {strip_ansi_codes(str(e))}"
            self.work_in_progress = False
            self.work_complete = False
            self.app.call_from_thread(show_spinner, False)
            self.app.call_from_thread(update_ui, "#clone-status", f"❌ {self.work_error}")
            if self.screen:
                self.app.call_from_thread(
                    lambda: setattr(self.screen.query_one("#next-btn", Button), "disabled", False)
                )
    def get_data(self) -> dict[str, Any]:
        """Get dbt path data."""
        # If input was a URL, it was updated to the local path during validate
        path = Path(self.input.value.strip()).expanduser().resolve()
        return {
            "dbt_path": str(path),
            "is_git_clone": self.was_git_clone  # Use persisted flag, not current URL check
        }


class DbtSubProjectStep(WizardStep):
    """Step 2b: Select dbt sub-project if multiple found."""

    def __init__(self):
        """Initialize dbt sub-project selection step."""
        super().__init__(
            title="Select dbt Project",
            description="Multiple dbt projects found. Select the one to use.",
            step_id="dbt-subproject",
        )
        self.project_select: Select | None = None
        self.manual_input: Input | None = None
        self.projects: list[Path] = []
        self.base_path: Path = Path()
        self.skip_step: bool = False
        self.needs_dbt_setup: bool = False  # True if we need to run dbt commands
        self.dbt_setup_complete: bool = False
        self.dbt_setup_in_progress: bool = False
        self.dbt_setup_error: Optional[str] = None

    def get_content(self) -> ComposeResult:
        """Get step content."""
        # Scan for projects first (before rendering UI)
        if self.screen and hasattr(self.screen, "wizard_data"):
            dbt_path_str = self.screen.wizard_data.get("dbt_path", "")
            self.base_path = Path(dbt_path_str).expanduser().resolve()

            # Check if subprojects were detected during clone (monorepo case)
            detected = self.screen.wizard_data.get("detected_subprojects", [])
            if detected:
                self.projects = [Path(p) for p in detected]
                self.needs_dbt_setup = True
            else:
                # Scan for dbt projects
                self.projects = find_dbt_projects(self.base_path, max_depth=3)
                self.needs_dbt_setup = True

            # If exactly one project at root, skip this step
            if len(self.projects) == 1 and self.projects[0] == self.base_path:
                self.skip_step = True
                if self.screen:
                    self.screen.wizard_data["dbt_project_root"] = str(self.base_path)

        if self.skip_step:
            yield Static("✅ Single dbt project found at repository root", classes="wizard-hint")
            return

        if len(self.projects) > 1:
            yield Label(f"Found {len(self.projects)} dbt projects:")

            # Show relative paths
            options = []
            for proj in self.projects:
                try:
                    rel_path = proj.relative_to(self.base_path)
                    display = str(rel_path) if str(rel_path) != "." else "(root)"
                except ValueError:
                    display = str(proj)
                options.append((display, str(proj)))

            self.project_select = Select(
                options=options,
                prompt="Select dbt project root",
                id="project-select",
            )
            yield self.project_select

            # Status for dbt setup
            yield Static(id="subproject-status", classes="wizard-hint")
            spinner = LoadingIndicator(id="subproject-spinner")
            spinner.display = False
            yield spinner
            yield Static(id="subproject-output", classes="wizard-hint")

        elif len(self.projects) == 1:
            # Single subproject found (not at root)
            yield Label(f"Found dbt project at: {self.projects[0]}")
            yield Static(id="subproject-status", classes="wizard-hint")
            spinner = LoadingIndicator(id="subproject-spinner")
            spinner.display = False
            yield spinner
            yield Static(id="subproject-output", classes="wizard-hint")

            # Auto-select it
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.screen.wizard_data["dbt_project_root"] = str(self.projects[0])

        elif len(self.projects) == 0:
            yield Static("⚠ No dbt_project.yml found in repository", classes="wizard-hint")
            yield Label("Enter the relative path to your dbt project:")
            self.manual_input = Input(
                placeholder="path/to/dbt_project",
                id="manual-subproject-input",
            )
            yield self.manual_input

    async def validate(self) -> tuple[bool, str]:
        """Validate selection."""
        if self.skip_step:
            return True, ""

        selected_path: Optional[Path] = None

        if len(self.projects) > 1:
            # Check for Select.BLANK (NoSelection) - it's truthy but not a valid selection
            if not self.project_select or not self.project_select.value or self.project_select.value == Select.BLANK:
                return False, "Please select a dbt project"
            selected_path = Path(str(self.project_select.value))
            if not (selected_path / "dbt_project.yml").exists():
                return False, f"No dbt_project.yml found at {selected_path}"
            # Store the selected project root
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.screen.wizard_data["dbt_project_root"] = str(selected_path)

        elif len(self.projects) == 1:
            selected_path = self.projects[0]
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.screen.wizard_data["dbt_project_root"] = str(selected_path)

        elif len(self.projects) == 0:
            if not self.manual_input or not self.manual_input.value.strip():
                return False, "Please enter the path to your dbt project"

            manual_path = self.base_path / self.manual_input.value.strip()
            if not manual_path.exists():
                return False, f"Path does not exist: {manual_path}"
            if not (manual_path / "dbt_project.yml").exists():
                return False, f"No dbt_project.yml found at {manual_path}"

            selected_path = manual_path
            if self.screen and hasattr(self.screen, "wizard_data"):
                self.screen.wizard_data["dbt_project_root"] = str(manual_path)

        # If we need to run dbt setup (monorepo case)
        if self.needs_dbt_setup and selected_path:
            if self.dbt_setup_error:
                return False, self.dbt_setup_error

            if not self.dbt_setup_complete:
                if not self.dbt_setup_in_progress:
                    self.run_dbt_setup(selected_path)
                return False, ""  # Wait for setup to complete

        return True, ""

    @work(thread=True)
    def run_dbt_setup(self, project_path: Path) -> None:
        """Run dbt deps and docs generate for selected subproject."""
        if self.dbt_setup_in_progress or self.dbt_setup_complete:
            return

        self.dbt_setup_in_progress = True
        self.dbt_setup_error = None

        # Create UI helpers
        update_ui = create_ui_updater(self)
        show_spinner = create_spinner_toggle(self, "subproject-spinner")

        # Disable Next button
        if self.screen:
            self.app.call_from_thread(
                lambda: setattr(self.screen.query_one("#next-btn", Button), "disabled", True)
            )

        self.app.call_from_thread(show_spinner, True)

        try:
            # Run dbt deps only (docs generate needs profile which comes later)
            run_dbt_deps(
                project_path, self.app, update_ui,
                status_selector="#subproject-status",
                output_selector="#subproject-output"
            )

            self.dbt_setup_complete = True
            self.dbt_setup_in_progress = False

            self.app.call_from_thread(show_spinner, False)
            if self.screen:
                def enable_next():
                    btn = self.screen.query_one("#next-btn", Button)
                    btn.disabled = False
                    btn.focus()
                self.app.call_from_thread(enable_next)

        except Exception as e:
            # Strip ANSI codes from error (dbt output may contain them)
            self.dbt_setup_error = f"dbt setup failed: {strip_ansi_codes(str(e))}"
            self.dbt_setup_in_progress = False
            self.app.call_from_thread(show_spinner, False)
            self.app.call_from_thread(update_ui, "#subproject-status", f"❌ {self.dbt_setup_error}")
            if self.screen:
                self.app.call_from_thread(
                    lambda: setattr(self.screen.query_one("#next-btn", Button), "disabled", False)
                )

    def get_data(self) -> dict[str, Any]:
        """Get selected project data."""
        if self.skip_step:
            return {}

        # Project root already stored in wizard_data during validate
        return {}

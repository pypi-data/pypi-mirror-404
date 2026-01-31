"""Helper functions, constants, and data classes for the init wizard.

This module contains shared utilities used across all init wizard steps.
"""
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from textual.app import App
from textual.css.query import NoMatches
from textual.widgets import Button, LoadingIndicator, Static

from lineage.tui.wizards.base import WizardStep
from lineage.utils.dbt import get_adapter_venv_dir, run_dbt_command

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

TYPEDEF_HOME = Path.home() / ".typedef"
TYPEDEF_PROFILES = TYPEDEF_HOME / "profiles"

# Regex to match ANSI escape sequences (colors, formatting, etc.)
ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')


# =============================================================================
# Path Helpers
# =============================================================================


def get_profiles_dir(project_name: str) -> Path:
    """Return the dbt profiles directory for a project."""
    return TYPEDEF_PROFILES / project_name


# =============================================================================
# String Utilities
# =============================================================================


def strip_ansi_codes(text: str) -> str:
    r"""Strip ANSI escape codes from text.

    Rich's escape_markup() only escapes Rich markup syntax like [bold],
    but ANSI codes like \x1b[0m contain literal [ characters that Rich
    interprets as markup. This function removes them entirely.

    Args:
        text: Text potentially containing ANSI escape codes

    Returns:
        Text with ANSI codes removed
    """
    return ANSI_ESCAPE_PATTERN.sub('', text)


# =============================================================================
# dbt Venv Management
# =============================================================================


def ensure_dbt_venv(adapter: str = "snowflake") -> Path:
    """Ensure a dbt venv exists for the adapter and dbt is installed.

    Creates a shared venv at ~/.typedef/venvs/dbt-{adapter}/ that can be
    used by all projects using the same adapter.

    Args:
        adapter: The dbt adapter to install (e.g., "snowflake", "bigquery")

    Returns:
        Path to the venv directory

    Raises:
        RuntimeError: If uv is not available
    """
    if not shutil.which("uv"):
        raise RuntimeError("uv is required to create a dbt venv")

    venv_dir = get_adapter_venv_dir(adapter)

    if not venv_dir.exists():
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["uv", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

    # Check if dbt is already installed
    dbt_bin = venv_dir / "bin" / "dbt"
    if not dbt_bin.exists():
        # Install dbt with loose version pinning for dbt-core
        subprocess.run(
            ["uv", "pip", "install", "--python", str(venv_dir / "bin" / "python"),
             "dbt-core>=1.7,<2.0", f"dbt-{adapter}>=1.7,<2.0"],
            check=True,
            capture_output=True,
            text=True,
        )

    return venv_dir


# =============================================================================
# File Operations
# =============================================================================


def upsert_env_file(env_path: Path, updates: dict[str, str]) -> None:
    """Create or update a .env file with provided values."""
    if not updates:
        return

    env_path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines: list[str] = []
    if env_path.exists():
        existing_lines = env_path.read_text().splitlines()

    updated_lines: list[str] = []
    seen_keys: set[str] = set()
    for line in existing_lines:
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if match:
            key = match.group(1)
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}")
                seen_keys.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    for key, value in updates.items():
        if key not in seen_keys:
            updated_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(updated_lines) + "\n")


# =============================================================================
# UI Update Helpers (Thread-Safe)
# =============================================================================


def create_ui_updater(step: WizardStep) -> Callable[[str, str], None]:
    """Create a UI update helper for background threads.

    Args:
        step: The wizard step containing the widgets

    Returns:
        A function that updates a Static widget by selector
    """
    def update_ui(selector: str, text: str) -> None:
        try:
            widget = step.query_one(selector, Static)
            widget.update(text)
        except NoMatches:
            pass
    return update_ui


def create_spinner_toggle(step: WizardStep, spinner_id: str) -> Callable[[bool], None]:
    """Create a spinner toggle helper for background threads.

    Args:
        step: The wizard step containing the spinner
        spinner_id: The ID of the LoadingIndicator widget

    Returns:
        A function that shows/hides the spinner
    """
    def show_spinner(visible: bool) -> None:
        try:
            spinner = step.query_one(f"#{spinner_id}", LoadingIndicator)
            spinner.display = visible
        except NoMatches:
            pass
    return show_spinner


def update_status(widget_id: str, message: str, app: App) -> None:
    """Thread-safe status widget update.

    Args:
        widget_id: CSS selector for widget (with or without #)
        message: Text to display
        app: The Textual app for call_from_thread
    """
    selector = f"#{widget_id}" if not widget_id.startswith("#") else widget_id

    def _update():
        try:
            widget = app.query_one(selector, Static)
            widget.update(message)
        except NoMatches:
            pass

    app.call_from_thread(_update)


def show_spinner_status(message: str, status_id: str, app: App) -> None:
    """Show spinner with message."""
    update_status(status_id, f"⏳ {message}", app)


def show_success(message: str, status_id: str, app: App) -> None:
    """Show success checkmark with message."""
    update_status(status_id, f"✅ {message}", app)


def show_error(message: str, status_id: str, app: App) -> None:
    """Show error message."""
    update_status(status_id, f"❌ {message}", app)


def set_button_disabled(button_id: str, disabled: bool, app: App) -> None:
    """Thread-safe button disabled state change."""
    selector = f"#{button_id}" if not button_id.startswith("#") else button_id

    def _update():
        try:
            btn = app.query_one(selector, Button)
            btn.disabled = disabled
        except NoMatches:
            pass

    app.call_from_thread(_update)


def focus_button(button_id: str, app: App) -> None:
    """Thread-safe button focus."""
    selector = f"#{button_id}" if not button_id.startswith("#") else button_id

    def _update():
        try:
            btn = app.query_one(selector, Button)
            btn.focus()
        except NoMatches:
            pass

    app.call_from_thread(_update)


# =============================================================================
# dbt Command Helpers
# =============================================================================


def run_dbt_deps(
    project_path: Path,
    app: App,
    update_ui: Callable[[str, str], None],
    adapter: str = "snowflake",
    status_selector: str = "#clone-status",
    output_selector: str = "#dbt-output",
) -> None:
    """Run dbt deps for a project (doesn't require profiles.yml).

    Args:
        project_path: Path to the dbt project
        app: The Textual app (for call_from_thread)
        update_ui: UI update helper function
        adapter: The dbt adapter to use for venv lookup
        status_selector: CSS selector for status widget
        output_selector: CSS selector for output widget
    """
    app.call_from_thread(update_ui, status_selector, "⏳ Running dbt deps...")
    try:
        venv_dir = ensure_dbt_venv(adapter)
        stdout, _stderr = run_dbt_command(
            ["deps"], project_path, profiles_dir=project_path, venv_dir=venv_dir
        )
        if stdout:
            # Strip ANSI codes to prevent Rich markup parsing errors
            clean_output = strip_ansi_codes(stdout[-500:])
            app.call_from_thread(update_ui, output_selector, f"dbt deps:\n{clean_output}")
        app.call_from_thread(update_ui, status_selector, "✅ dbt deps complete")
    except subprocess.CalledProcessError as e:
        error_msg = f"⚠ dbt deps failed (exit {e.returncode})"
        if e.stderr:
            # Strip ANSI codes from stderr as well
            clean_stderr = strip_ansi_codes(e.stderr[-500:])
            error_msg += f"\n{clean_stderr}"
        app.call_from_thread(update_ui, output_selector, error_msg)
        # Continue anyway


# =============================================================================
# dbt Project Utilities
# =============================================================================


def get_dbt_profile_name(project_path: Path) -> Optional[str]:
    """Extract the profile name from dbt_project.yml.

    Args:
        project_path: Path to directory containing dbt_project.yml

    Returns:
        Profile name if found, None otherwise
    """
    import yaml

    dbt_project_file = project_path / "dbt_project.yml"
    if not dbt_project_file.exists():
        return None

    try:
        with open(dbt_project_file) as f:
            config = yaml.safe_load(f)
        return config.get("profile")
    except (OSError, yaml.YAMLError):
        return None


def find_dbt_projects(root_path: Path, max_depth: int = 3) -> list[Path]:
    """Find all dbt_project.yml files within a directory tree.

    Args:
        root_path: Root directory to search from
        max_depth: Maximum depth to search (default 3)

    Returns:
        List of paths to directories containing dbt_project.yml
    """
    projects = []

    def search(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for item in path.iterdir():
                if item.is_file() and item.name == "dbt_project.yml":
                    projects.append(item.parent)
                elif item.is_dir() and not item.name.startswith(".") and not item.name.startswith("dbt_packages"):
                    search(item, depth + 1)
        except (PermissionError, OSError):
            pass

    search(root_path, 0)
    return sorted(projects)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SnowflakeCredentials:
    """Container for Snowflake connection credentials (key-based auth)."""

    account: str
    user: str
    role: str
    warehouse: str
    private_key_path: str
    database: str = ""
    schema: str = ""

    def validate_required(self) -> tuple[bool, str]:
        """Check all required fields are present.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.account:
            return False, "Account identifier is required"
        if not self.user:
            return False, "Username is required"
        if not self.private_key_path:
            return False, "Private key path is required"
        # Validate key file exists
        key_path = Path(self.private_key_path).expanduser()
        if not key_path.exists():
            return False, f"Private key not found: {key_path}"
        return True, ""

    def to_dict(self) -> dict[str, str]:
        """Convert to dict for passing to Snowflake functions."""
        return {
            "account": self.account,
            "user": self.user,
            "role": self.role,
            "warehouse": self.warehouse,
            "private_key_path": self.private_key_path,
        }


@dataclass
class DbtProjectInfo:
    """Resolved dbt project information."""

    root_path: Path
    target_path: Path
    profile_name: str
    is_monorepo: bool
    subprojects: list[Path]
    was_cloned: bool
    needs_profile_generation: bool

    @classmethod
    def from_path(cls, path: str, was_cloned: bool = False) -> "DbtProjectInfo":
        """Resolve dbt project from path.

        Args:
            path: Path to dbt project directory
            was_cloned: Whether this project was cloned from git

        Returns:
            DbtProjectInfo with resolved paths and metadata
        """
        root = Path(path).expanduser().resolve()

        # Check for monorepo (multiple projects or no project at root)
        subprojects = find_dbt_projects(root, max_depth=3)
        has_root_project = (root / "dbt_project.yml").exists()
        is_monorepo = not has_root_project and len(subprojects) > 0

        # Get profile name from dbt_project.yml
        profile_name = get_dbt_profile_name(root) or "dev"

        # Check if profiles.yml exists
        needs_profile = not (root / "profiles.yml").exists()

        return cls(
            root_path=root,
            target_path=root / "target",
            profile_name=profile_name,
            is_monorepo=is_monorepo,
            subprojects=subprojects,
            was_cloned=was_cloned,
            needs_profile_generation=needs_profile,
        )

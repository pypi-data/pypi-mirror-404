"""typedef CLI - Local-first Data Concierge.

This module provides the simplified CLI for the typedef Data Intelligence Platform.
All commands use ~/.typedef/ as the default configuration and data directory.

Commands:
    typedef init      - Interactive setup wizard
    typedef sync      - Load dbt project into graph
    typedef chat      - Launch TUI chat interface
    typedef export    - Export graph for team sharing
    typedef import    - Import graph from teammate
    typedef config    - Show/validate configuration
"""

from __future__ import annotations

# Suppress warnings as early as possible to catch C extension warnings
import os  # noqa: I001 - must be imported first
import sys
import atexit
import warnings

# Set PYTHONWARNINGS for any subprocesses that might be spawned
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning,ignore::UserWarning"

# Disable tqdm progress bars from fenic BEFORE any imports
# This must be set before tqdm is imported anywhere
os.environ["TQDM_DISABLE"] = "1"

# Silence deprecation warnings for end users
# These are internal issues we'll fix, but users shouldn't see them
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", UserWarning)


# Re-suppress warnings at exit (for C extension cleanup warnings like swigvarlink)
@atexit.register
def _suppress_exit_warnings():
    warnings.simplefilter("ignore")

warnings.filterwarnings("ignore", message=".*class-based.*config.*is deprecated.*")
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince20.*")
warnings.filterwarnings("ignore", message="Field name .* shadows an attribute")
warnings.filterwarnings("ignore", message=".*swigvarlink.*")
# LanceDB fork safety warning (UserWarning, not DeprecationWarning)
warnings.filterwarnings("ignore", message=".*lance is not fork-safe.*")
# Multiprocessing fork warning with threads
warnings.filterwarnings("ignore", message=".*multi-threaded.*use of fork.*")
# sqlite3 datetime adapter deprecation (Python 3.12+)
warnings.filterwarnings("ignore", message=".*default datetime adapter is deprecated.*")

# Import remaining modules (must come after warning configuration)
# fmt: off
# ruff: noqa: E402, I001
import importlib.metadata  # noqa: E402
import logging  # noqa: E402
import shutil  # noqa: E402
import signal  # noqa: E402
import tarfile  # noqa: E402
import time  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Optional  # noqa: E402

import click  # noqa: E402
import yaml  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from lineage.backends.config import UnifiedConfig  # noqa: E402
from lineage.backends.data_query.factory import create_data_backend_for_cli  # noqa: E402
from lineage.backends.lineage.factory import create_storage_for_cli  # noqa: E402
from lineage.ingest.config import PopulationConfig  # noqa: E402
from lineage.ingest.progress import ProgressTracker, RichProgressHandler  # noqa: E402
from lineage.integration import load_full_lineage  # noqa: E402
from lineage.templates import render_typedef_config  # noqa: E402
from lineage.tui.app import main as tui_main  # noqa: E402
from lineage.tui.wizards.base import BaseWizardApp  # noqa: E402
from lineage.tui.wizards.init import (  # noqa: E402
    InitWizardApp,
    create_add_project_wizard,
)
from lineage.tui.wizards.project_selector import ProjectSelectorApp
from lineage.utils.env import load_env_file

# Default paths
TYPEDEF_HOME = Path.home() / ".typedef"
TYPEDEF_CONFIG = TYPEDEF_HOME / "config.yaml"
TYPEDEF_GRAPH_DB = TYPEDEF_HOME / "graph.db"
TYPEDEF_EXPORTS = TYPEDEF_HOME / "exports"
TYPEDEF_SESSIONS = TYPEDEF_HOME / "sessions"
TYPEDEF_LOGS = TYPEDEF_HOME / "logs"
TYPEDEF_PROFILES = TYPEDEF_HOME / "profiles"

# Semantic cache location (relative to dbt project)
SEMANTIC_CACHE_DIR = ".lineage_workspace/semantic_cache"

logger = logging.getLogger(__name__)


def get_version() -> str:
    """Get the package version from installed metadata."""
    try:
        return importlib.metadata.version("typedef-data-intelligence")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0-dev"


def get_typedef_home() -> Path:
    """Get the typedef home directory, creating it if needed."""
    TYPEDEF_HOME.mkdir(parents=True, exist_ok=True)
    return TYPEDEF_HOME


def get_config_path() -> Path:
    """Get the typedef config path."""
    return TYPEDEF_CONFIG


def save_config_atomic(config: dict) -> None:
    """Save config to file atomically to prevent corruption on crash/interrupt.

    Writes to a temp file in the same directory, then atomically renames.
    This ensures the config file is never in a partial/corrupted state.
    """
    import tempfile

    # Write to temp file in same directory (required for atomic rename)
    fd, temp_path = tempfile.mkstemp(
        dir=TYPEDEF_CONFIG.parent,
        prefix=".config.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        # Atomic rename (same filesystem guaranteed by same directory)
        os.replace(temp_path, TYPEDEF_CONFIG)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def ensure_typedef_dirs():
    """Ensure all typedef directories exist."""
    for dir_path in [TYPEDEF_HOME, TYPEDEF_EXPORTS, TYPEDEF_SESSIONS, TYPEDEF_LOGS, TYPEDEF_PROFILES]:
        dir_path.mkdir(parents=True, exist_ok=True)


# Note: Config templates have been moved to lineage/templates/typedef_config.yaml.j2
# The render_typedef_config() function generates the unified config.


# ============================================================================
# CLI Group
# ============================================================================

@click.group()
@click.version_option(version=get_version(), prog_name="typedef")
def main():
    """Typedef - Local-first Data Concierge.

    Get started:

        typedef init        # Setup wizard

        typedef sync        # Load your dbt project

        typedef chat        # Start chatting with your data
    """
    pass


# ============================================================================
# typedef init - Interactive Setup Wizard
# ============================================================================

@main.command()
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--reset", is_flag=True, help="Delete ~/.typedef first (fresh start)")
def init(force: bool, reset: bool):
    """Initialize typedef with an interactive TUI wizard.

    This launches a beautiful TUI wizard to create ~/.typedef/config.yaml
    with your project settings.
    """
    # Handle --reset flag
    if reset and TYPEDEF_HOME.exists():
        click.echo(f"🗑️  Resetting {TYPEDEF_HOME}...")
        shutil.rmtree(TYPEDEF_HOME)

    ensure_typedef_dirs()

    if TYPEDEF_CONFIG.exists() and not force:
        click.echo(f"⚠️  Configuration already exists at {TYPEDEF_CONFIG}")
        click.echo("Options:")
        click.echo("   `typedef projects add`: Add a new dbt project to your existing configuration")
        click.echo("   `typedef init --force`: Overwrite existing configuration")
        click.echo("   `typedef init --reset`: Delete ~/.typedef first (fresh start)")
        return

    # Launch TUI wizard
    app = InitWizardApp()
    result = app.run()

    if result is None:
        click.echo("Setup cancelled.")
        return

    # Load env vars written by wizard (Linear keys, Logfire token, etc.)
    load_env_file()

    # Extract wizard data
    project_name = result.get("project_name")
    dbt_path = result.get("dbt_path")
    dbt_project_root = result.get("dbt_project_root", dbt_path)  # Use sub-project root if specified
    snowflake_account = result.get("snowflake_account")
    snowflake_user = result.get("snowflake_user")
    snowflake_warehouse = result.get("snowflake_warehouse")
    snowflake_role = result.get("snowflake_role")
    snowflake_database = result.get("snowflake_database")
    allowed_databases = result.get("allowed_databases", [snowflake_database])
    # Schema default is PUBLIC, but user might have entered something else in connection step
    # However, database selection step overrides "default" selection
    snowflake_schema = result.get("snowflake_schema", "PUBLIC")  # Default for connection string, but allowed_schemas will be empty
    snowflake_private_key_path = result.get("snowflake_private_key_path")
    profile_name = result.get("profile_name", "dev")
    project_env_vars = result.get("project_env_vars", {})

    # Profile generation and dbt docs generate are now handled in the wizard
    # (DbtDocsGenerateStep) so we skip them here.

    # Detect Linear ticketing - ALL THREE env vars required
    linear_analyst_key = os.getenv("LINEAR_ANALYST_API_KEY")
    linear_de_key = os.getenv("LINEAR_DATA_ENGINEER_API_KEY")
    linear_team_id = os.getenv("LINEAR_TEAM_ID")

    # Enable Linear only if ALL THREE are present
    if linear_analyst_key and linear_de_key and linear_team_id:
        ticket_enabled = True
        ticket_backend = "linear"
        click.echo("✅ Detected Linear configuration - enabling Linear ticketing")
    else:
        # Disable ticketing when Linear keys are not fully configured
        ticket_enabled = False
        ticket_backend = "filesystem"
        # Show warning if partially configured
        missing = []
        if not linear_analyst_key:
            missing.append("LINEAR_ANALYST_API_KEY")
        if not linear_de_key:
            missing.append("LINEAR_DATA_ENGINEER_API_KEY")
        if not linear_team_id:
            missing.append("LINEAR_TEAM_ID")
        if missing and len(missing) < 3:  # Partially configured
            click.echo(f"⚠️  Linear ticketing disabled - missing: {', '.join(missing)}")

    # Generate unified config using Jinja2 template
    # This single file is used for both sync and chat commands
    config_content = render_typedef_config(
        project_name=project_name,
        dbt_path=str(dbt_project_root),
        graph_db_path=str(TYPEDEF_GRAPH_DB),
        typedef_home=str(TYPEDEF_HOME),
        profiles_dir=str(TYPEDEF_PROFILES / project_name),
        snowflake_account=snowflake_account,
        snowflake_user=snowflake_user,
        snowflake_warehouse=snowflake_warehouse,
        snowflake_role=snowflake_role,
        snowflake_database=snowflake_database,
        snowflake_schema=snowflake_schema,
        snowflake_private_key_path=snowflake_private_key_path,
        profile_name=profile_name,
        allowed_databases=allowed_databases,
        allowed_schemas=[],  # All schemas allowed by default
        default_database=snowflake_database,
        project_env_vars=project_env_vars if project_env_vars else None,
        git_enabled=True,
        git_working_directory=str(dbt_project_root),
        ticket_enabled=ticket_enabled,
        ticket_backend=ticket_backend,
        linear_team_id=linear_team_id,
        linear_mcp_server_url="https://mcp.linear.app/mcp",
    )

    # Write unified config
    TYPEDEF_CONFIG.write_text(config_content)

    # Initialize the graph database with schema (creates indices)
    try:
        unified_cfg = UnifiedConfig.from_yaml(TYPEDEF_CONFIG)
        storage = create_storage_for_cli(unified_cfg.lineage)
        storage.recreate_schema()
        click.echo(f"✅ Initialized graph database at {TYPEDEF_GRAPH_DB}")
    except Exception as e:
        click.echo(f"⚠️  Could not initialize graph database: {e}")
        click.echo("   Graph will be initialized on first sync.")

    click.echo()
    click.echo(f"✅ Configuration saved to {TYPEDEF_CONFIG}")
    click.echo()
    click.echo("🎉 Setup complete! Next steps:")
    click.echo()
    click.echo("   1. Ingest dbt Project into Knowledge Graph:         typedef sync")
    click.echo("   2. Start chatting with your data:          typedef chat")


# ============================================================================
# typedef sync - Load dbt project into graph
# ============================================================================

@main.command()
@click.argument("projects", nargs=-1, required=False)
@click.option("--all", is_flag=True, help="Sync all configured projects")
@click.option("--full", is_flag=True, help="Force complete resync (ignore cache)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def sync(projects: tuple[str, ...], all: bool, full: bool, verbose: bool):
    """Sync dbt project(s) to the local graph.

    This parses dbt manifests, runs semantic analysis, and loads
    everything into the embedded FalkorDB Lite graph database.

    Examples:
        typedef sync                    # Sync default project
        typedef sync my_analytics       # Sync specific project
        typedef sync proj1 proj2        # Sync multiple projects
        typedef sync --all              # Sync all projects
    """
    load_env_file()

    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    # Load config
    with open(TYPEDEF_CONFIG) as f:
        config = yaml.safe_load(f)

    # Get projects configuration
    project_configs = config.get("projects", {})
    default_project = config.get("default_project")

    if not project_configs:
        click.echo("❌ No projects configured. Run 'typedef init' first.")
        sys.exit(1)

    # Determine which projects to sync
    if all:
        projects_to_sync = list(project_configs.keys())
    elif projects:
        # Validate all specified projects exist
        for p in projects:
            if p not in project_configs:
                click.echo(f"❌ Project '{p}' not found in configuration")
                click.echo(f"   Available projects: {', '.join(project_configs.keys())}")
                sys.exit(1)
        projects_to_sync = list(projects)
    else:
        # Use default project
        if not default_project:
            click.echo("❌ No default project set. Specify project name or use --all")
            sys.exit(1)
        projects_to_sync = [default_project]

    # Setup logging
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai.models").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)

    click.echo(f"🔄 Syncing {len(projects_to_sync)} project(s)...")
    click.echo()

    # Load unified config (contains lineage, data, projects, and population settings)
    unified_cfg = UnifiedConfig.from_yaml(TYPEDEF_CONFIG)

    # Create storage (shared across all projects, different graphs)
    storage = create_storage_for_cli(unified_cfg.lineage)
    storage.ensure_schema()  # Ensure indices exist (idempotent)

    # Get population settings from unified config
    if unified_cfg.population:
        pop = PopulationConfig(**unified_cfg.population)
    else:
        pop = PopulationConfig()

    # Sync each project
    total_start = time.time()
    successful = []
    failed = []
    failed_errors: dict[str, str] = {}

    # Set up signal handler to ensure Ctrl+C works even with background threads
    def sigint_handler(_signum, _frame):
        raise KeyboardInterrupt()

    original_handler = signal.signal(signal.SIGINT, sigint_handler)

    # Use Rich progress display
    console = Console()
    interrupted = False

    try:
        with RichProgressHandler() as progress_handler:
            tracker = ProgressTracker(callback=progress_handler)

            for idx, project_name in enumerate(projects_to_sync, 1):
                project_config = project_configs[project_name]
                dbt_path = Path(project_config.get("dbt_path", "."))
                graph_name = project_config.get("graph_name", project_name)

                # Load project-specific env vars (non-secret)
                project_env_vars = project_config.get("env", {})
                if project_env_vars:
                    for key, value in project_env_vars.items():
                        os.environ[key] = str(value)

                # Print project header using Rich console
                console.print(f"\n[bold blue][{idx}/{len(projects_to_sync)}] {project_name}[/bold blue]")
                console.print(f"   dbt path: {dbt_path}", style="dim")
                console.print(f"   Graph: {graph_name}", style="dim")

                # Create data backend with per-project overrides
                # Check if project has data overrides in unified config
                try:
                    data_config = unified_cfg.get_project_data_config(project_name)
                except KeyError:
                    # Project not in unified config projects, use base config
                    data_config = unified_cfg.data
                data_backend = create_data_backend_for_cli(data_config, read_only=True)

                # Find target directory
                target_dir = dbt_path / "target"
                if not target_dir.exists():
                    error_msg = "No target/ directory found. Run 'dbt compile' first."
                    console.print(f"   [red]❌ {error_msg}[/red]")
                    failed.append(project_name)
                    failed_errors[project_name] = error_msg
                    continue

                manifest_path = target_dir / "manifest.json"
                if not manifest_path.exists():
                    error_msg = "No manifest.json found. Run 'dbt compile' first."
                    console.print(f"   [red]❌ {error_msg}[/red]")
                    failed.append(project_name)
                    failed_errors[project_name] = error_msg
                    continue

                # Set active graph for this project
                if hasattr(storage, 'set_active_graph'):
                    storage.set_active_graph(graph_name)

                try:
                    start_time = time.time()

                    # Run full lineage load with progress tracking
                    # Pass TYPEDEF_HOME as fenic_db_path so DuckDB and LLM cache
                    # are stored in ~/.typedef/ instead of current directory
                    load_full_lineage(
                        artifacts_dir=target_dir,
                        storage=storage,
                        semantic_config=pop.semantic_analysis,
                        profiling_config=pop.profiling,
                        clustering_config=pop.clustering,
                        semantic_view_config=pop.semantic_view_loader,
                        data_backend=data_backend,
                        model_filter=pop.semantic_analysis.model_filter,
                        incremental=not full,
                        verbose=verbose,
                        graph_name=graph_name,
                        progress_tracker=tracker,
                        fenic_db_path=TYPEDEF_HOME,
                    )

                    elapsed = time.time() - start_time
                    console.print(f"   [green]✅ Synced in {elapsed:.1f}s[/green]")
                    successful.append(project_name)
                except KeyboardInterrupt:
                    raise  # Re-raise to exit the outer try block
                except Exception as e:
                    error_msg = str(e).strip() or "Unknown error"
                    console.print(f"   [red]❌ Error: {error_msg}[/red]")
                    failed.append(project_name)
                    failed_errors[project_name] = error_msg

    except KeyboardInterrupt:
        interrupted = True
        console.print("\n[yellow]⚠️  Sync interrupted by user[/yellow]")

    # Summary
    total_elapsed = time.time() - total_start
    console.print()
    console.print("=" * 60)
    if interrupted:
        console.print(f"[yellow]⚠️  Sync interrupted after {total_elapsed:.1f}s[/yellow]")
    console.print(f"[green]✅ {len(successful)} project(s) synced successfully[/green]")
    if failed:
        console.print(f"[red]❌ {len(failed)} project(s) failed: {', '.join(failed)}[/red]")
        for project in failed:
            error_msg = failed_errors.get(project, "Unknown error")
            if len(error_msg) > 200:
                error_msg = error_msg[:200].rstrip() + "..."
            console.print(f"   [red]- {project}: {error_msg}[/red]")
    if not interrupted:
        console.print()
        console.print("   Next: [bold]typedef chat[/bold]")

    # Restore original signal handler
    signal.signal(signal.SIGINT, original_handler)

    # Close storage to release embedded resources (e.g., FalkorDBLite)
    storage.close()


# ============================================================================
# typedef chat - Launch TUI
# ============================================================================

@main.command()
@click.argument("project", required=False)
@click.option("--select", "-s", is_flag=True, help="Show interactive project selector")
@click.option("--daemon", "-d", is_flag=True, help="Start in autonomous daemon mode")
def chat(project: Optional[str], select: bool, daemon: bool):
    """Launch the Data Concierge TUI chat interface.

    Starts an interactive terminal UI where you can chat with your data
    using the Analyst, Investigator, Insights, and Copilot agents.

    Use --daemon to start in autonomous mode, which automatically
    processes tickets without user interaction.

    Examples:
        typedef chat                    # Use default project
        typedef chat my_analytics       # Use specific project
        typedef chat --select           # Show interactive project selector
        typedef chat --daemon           # Start in autonomous daemon mode
    """
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    # Load config
    with open(TYPEDEF_CONFIG) as f:
        config = yaml.safe_load(f)

    projects = config.get("projects", {})
    default_project = config.get("default_project")

    if not projects:
        click.echo("❌ No projects configured. Run 'typedef init' first.")
        sys.exit(1)

    # Determine which project to use
    if select or (project is None and len(projects) > 1):
        # Launch TUI project selector
        selector_app = ProjectSelectorApp(projects, default_project)
        selector_app.run()

        if selector_app.selected is None:
            click.echo("Cancelled.")
            return

        project_name = selector_app.selected
    elif project:
        # Validate specified project
        if project not in projects:
            click.echo(f"❌ Project '{project}' not found in configuration")
            click.echo(f"   Available projects: {', '.join(projects.keys())}")
            sys.exit(1)
        project_name = project
    else:
        # Use default project
        if not default_project:
            click.echo("❌ No default project set. Use --select or specify project name.")
            sys.exit(1)
        project_name = default_project

    # Get project config
    project_config = projects[project_name]
    graph_name = project_config.get("graph_name", project_name)
    profiles_dir = project_config.get("profiles_dir")
    if not profiles_dir:
        profiles_dir = str(TYPEDEF_PROFILES / project_name)

    # Set environment for the TUI
    os.environ["UNIFIED_CONFIG"] = str(TYPEDEF_CONFIG)
    os.environ["TYPEDEF_ACTIVE_PROJECT"] = project_name
    os.environ["TYPEDEF_GRAPH_NAME"] = graph_name

    # Pass the dbt project path for the copilot working directory
    dbt_path = project_config.get("dbt_path")
    if dbt_path:
        os.environ["GIT_WORKING_DIR"] = str(Path(dbt_path).expanduser().resolve())
    if profiles_dir:
        os.environ["DBT_PROFILES_DIR"] = str(Path(profiles_dir).expanduser().resolve())

    # Load project-specific env vars (non-secret)
    project_env_vars = project_config.get("env", {})
    if project_env_vars:
        for key, value in project_env_vars.items():
            os.environ[key] = str(value)
        click.echo(f"✅ Loaded {len(project_env_vars)} project env var(s)")

    # Ensure logs directory exists
    TYPEDEF_LOGS.mkdir(parents=True, exist_ok=True)

    # Pass daemon mode flag to TUI via environment
    if daemon:
        os.environ["TYPEDEF_DAEMON_MODE"] = "1"
        click.echo("🤖 Starting in autonomous daemon mode...")

    # Run TUI
    tui_main()


# ============================================================================
# typedef project - Quick project selection
# ============================================================================

@main.command("project")
@click.argument("project_name", required=False)
@click.option("--select", "-s", is_flag=True, help="Show interactive project selector")
def project_select(project_name: Optional[str], select: bool):
    """Show or switch the current default project.

    Without arguments, shows the current default project.
    With a project name, switches to that project.
    With --select, shows an interactive TUI selector.

    Examples:
        typedef project                # Show current project
        typedef project my_analytics   # Switch to my_analytics
        typedef project --select       # Interactive selector
    """
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    with open(TYPEDEF_CONFIG) as f:
        config = yaml.safe_load(f)

    project_configs = config.get("projects", {})
    default_project = config.get("default_project")

    if not project_configs:
        click.echo("❌ No projects configured. Run 'typedef init' first.")
        sys.exit(1)

    # Interactive selector mode
    if select or (project_name is None and len(project_configs) > 1):
        selector_app = ProjectSelectorApp(project_configs, default_project)
        selector_app.run()

        if selector_app.selected is None:
            click.echo("Cancelled.")
            return

        project_name = selector_app.selected

    # If no project specified and only one project, just show it
    if project_name is None:
        if default_project:
            console = Console()
            console.print(f"Current project: [bold cyan]{default_project}[/bold cyan]")
            proj = project_configs.get(default_project, {})
            console.print(f"   dbt path: {proj.get('dbt_path', 'N/A')}", style="dim")
        else:
            click.echo("No default project set.")
            click.echo("Run 'typedef project --select' to choose one.")
        return

    # Switch to specified project
    if project_name not in project_configs:
        click.echo(f"❌ Project '{project_name}' not found")
        click.echo(f"   Available: {', '.join(project_configs.keys())}")
        sys.exit(1)

    if project_name == default_project:
        click.echo(f"Already using project: {project_name}")
        return

    # Update default project
    config["default_project"] = project_name

    with open(TYPEDEF_CONFIG, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✅ Switched to project: {project_name}")


# ============================================================================
# typedef projects - Manage multiple projects
# ============================================================================

@main.group()
def projects():
    """Manage multiple dbt projects."""
    pass


@projects.command("list")
def projects_list():
    """List all configured projects."""
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    with open(TYPEDEF_CONFIG) as f:
        config = yaml.safe_load(f)

    project_configs = config.get("projects", {})
    default_project = config.get("default_project")

    if not project_configs:
        click.echo("No projects configured yet.")
        return

    # Use rich tables for nice output
    console = Console()
    table = Table(title="typedef Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="blue")
    table.add_column("Graph", style="magenta")
    table.add_column("Status", style="green")

    for name, proj in project_configs.items():
        is_default = name == default_project
        status = "✅ default" if is_default else ""

        # Check if project has been synced
        graph_name = proj.get("graph_name", name)
        # For now we just show the graph name, checking sync status requires DB access

        table.add_row(
            name,
            proj.get("dbt_path", "N/A"),
            graph_name,
            status
        )

    console.print(table)


@projects.command("add")
def projects_add():
    """Add a new project to the configuration.

    Launches a TUI wizard to interactively configure a new project,
    including Snowflake connection settings specific to this project.
    """
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    # Load existing config to check for duplicate project names
    with open(TYPEDEF_CONFIG) as f:
        existing_config = yaml.safe_load(f)

    # Create full wizard for adding a project (same steps as init)
    wizard = create_add_project_wizard()
    app = BaseWizardApp(wizard)
    result = app.run()

    if result is None:
        click.echo("Cancelled.")
        return

    project_name = result["project_name"]

    # Check if project already exists
    if project_name in existing_config.get("projects", {}):
        click.echo(f"❌ Project '{project_name}' already exists in configuration")
        sys.exit(1)

    # Extract all wizard results
    dbt_path = result.get("dbt_project_root") or result.get("dbt_path")
    profile_name = result.get("profile_name", "default")
    snowflake_database = result.get("snowflake_database")
    snowflake_schema = result.get("snowflake_schema")
    allowed_databases = result.get("allowed_databases", [])
    project_env_vars = result.get("project_env_vars")

    # Snowflake connection details for per-project override
    result.get("snowflake_account")
    result.get("snowflake_user")
    snowflake_warehouse = result.get("snowflake_warehouse")
    snowflake_role = result.get("snowflake_role")
    result.get("snowflake_private_key_path")

    # Build project config
    project_config = {
        "name": project_name,
        "dbt_path": str(dbt_path),
        "graph_name": project_name,
        "profile_name": profile_name,
        "profiles_dir": str(TYPEDEF_PROFILES / project_name),
    }

    # Add optional fields
    if allowed_databases:
        project_config["allowed_databases"] = allowed_databases
    if snowflake_database:
        project_config["default_database"] = snowflake_database
    if project_env_vars:
        project_config["env"] = project_env_vars

    # Add git configuration (per-project)
    project_config["git"] = {
        "enabled": True,
        "working_directory": str(dbt_path)
    }

    # Add per-project data override if different from global config
    global_data = existing_config.get("data", {})
    needs_data_override = (
        snowflake_database and snowflake_database != global_data.get("database")
    ) or (
        snowflake_schema and snowflake_schema != global_data.get("schema_name")
    ) or (
        snowflake_warehouse and snowflake_warehouse != global_data.get("warehouse")
    ) or (
        snowflake_role and snowflake_role != global_data.get("role")
    )

    if needs_data_override:
        project_config["data"] = {}
        if snowflake_database:
            project_config["data"]["database"] = snowflake_database
        if snowflake_schema:
            project_config["data"]["schema_name"] = snowflake_schema
        if snowflake_warehouse and snowflake_warehouse != global_data.get("warehouse"):
            project_config["data"]["warehouse"] = snowflake_warehouse
        if snowflake_role and snowflake_role != global_data.get("role"):
            project_config["data"]["role"] = snowflake_role

    # Add new project to config
    if "projects" not in existing_config:
        existing_config["projects"] = {}

    existing_config["projects"][project_name] = project_config

    # Save config atomically
    save_config_atomic(existing_config)

    click.echo(f"✅ Added project: {project_name}")
    click.echo(f"   dbt path: {dbt_path}")
    click.echo(f"   git enabled: yes (working_dir: {dbt_path})")
    if snowflake_database:
        click.echo(f"   database: {snowflake_database}")
    if snowflake_schema:
        click.echo(f"   schema: {snowflake_schema}")
    click.echo()

    if click.confirm("Would you like to sync this project now?"):
        # Call sync for this project
        from lineage.typedef_cli import sync as sync_cmd
        ctx = click.get_current_context()
        ctx.invoke(sync_cmd, projects=(project_name,), all=False, full=False, verbose=False)


@projects.command("remove")
@click.argument("project_name")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def projects_remove(project_name: str, force: bool):
    """Remove a project from the configuration.

    This removes the project from the config file but does NOT delete
    the graph data. The graph remains in the database file.
    """
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    with open(TYPEDEF_CONFIG) as f:
        config = yaml.safe_load(f)

    projects_cfg = config.get("projects", {})

    if project_name not in projects_cfg:
        click.echo(f"❌ Project '{project_name}' not found in configuration")
        sys.exit(1)

    # Confirm removal
    if not force:
        click.echo(f"⚠️  Remove project '{project_name}' from configuration?")
        click.echo("   (Graph data will remain in the database)")
        if not click.confirm("Continue?"):
            click.echo("Cancelled.")
            return

    # Remove project
    del config["projects"][project_name]

    # Update default if needed
    if config.get("default_project") == project_name:
        remaining = list(config["projects"].keys())
        if remaining:
            config["default_project"] = remaining[0]
            click.echo(f"   Updated default project to: {remaining[0]}")
        else:
            config["default_project"] = None

    # Save config atomically
    save_config_atomic(config)

    click.echo(f"✅ Removed project: {project_name}")


@projects.command("set-default")
@click.argument("project_name")
def projects_set_default(project_name: str):
    """Set the default project.

    The default project is used when running commands without specifying
    a project explicitly.
    """
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    with open(TYPEDEF_CONFIG) as f:
        config = yaml.safe_load(f)

    projects_cfg = config.get("projects", {})

    if project_name not in projects_cfg:
        click.echo(f"❌ Project '{project_name}' not found in configuration")
        sys.exit(1)

    config["default_project"] = project_name

    # Save config atomically
    save_config_atomic(config)

    click.echo(f"✅ Set default project to: {project_name}")


# ============================================================================
# typedef export - Export graph for sharing
# ============================================================================

@main.command("export")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def export_graph(output: Optional[str]):
    """Export the graph and semantic cache for team sharing.

    Creates a compressed archive containing:
    - FalkorDB Lite database file
    - Semantic analysis cache (parquet files)

    Teammates can import this with 'typedef import'.
    """
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    if not TYPEDEF_GRAPH_DB.exists():
        click.echo("❌ No graph database found. Run 'typedef sync' first.")
        sys.exit(1)

    # Load config for project name and dbt path
    with open(TYPEDEF_CONFIG) as f:
        config = yaml.safe_load(f)

    project_config = config.get("project", {})
    project_name = project_config.get("name", "unknown")
    dbt_path = Path(project_config.get("dbt_path", "."))

    # Determine output path
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if output:
        output_path = Path(output)
    else:
        TYPEDEF_EXPORTS.mkdir(parents=True, exist_ok=True)
        output_path = TYPEDEF_EXPORTS / f"{project_name}-{timestamp}.typedef.tar.gz"

    click.echo(f"📦 Exporting {project_name}...")

    # Create tarball
    with tarfile.open(output_path, "w:gz") as tar:
        # Add graph database
        click.echo("   Adding graph database...")
        tar.add(TYPEDEF_GRAPH_DB, arcname="graph.db")

        # Add semantic cache if it exists
        semantic_cache = dbt_path / SEMANTIC_CACHE_DIR / project_name
        if semantic_cache.exists():
            click.echo("   Adding semantic cache...")
            tar.add(semantic_cache, arcname=f"semantic_cache/{project_name}")

        # Add config (without sensitive data)
        # We create a sanitized version
        click.echo("   Adding project metadata...")
        metadata = {
            "project_name": project_name,
            "exported_at": datetime.now().isoformat(),
            "typedef_version": get_version(),
        }
        metadata_path = TYPEDEF_HOME / "export_metadata.yaml"
        with open(metadata_path, "w") as f:
            yaml.safe_dump(metadata, f)
        tar.add(metadata_path, arcname="metadata.yaml")
        metadata_path.unlink()  # Clean up temp file

    # Get file size
    file_size = output_path.stat().st_size
    size_mb = file_size / (1024 * 1024)

    click.echo()
    click.echo(f"✅ Exported to: {output_path}")
    click.echo(f"   Size: {size_mb:.2f} MB")
    click.echo()
    click.echo("   Share this file with teammates. They can import with:")
    click.echo(f"   typedef import {output_path.name}")


# ============================================================================
# typedef import - Import graph from teammate
# ============================================================================

@main.command("import")
@click.argument("archive_path", type=click.Path(exists=True))
@click.option("--force", is_flag=True, help="Overwrite existing graph")
def import_graph(archive_path: str, force: bool):
    """Import a graph archive from a teammate.

    This extracts:
    - Graph database to ~/.typedef/graph.db
    - Semantic cache to your dbt project's cache directory

    Skips semantic analysis since the cache is already populated.
    """
    archive = Path(archive_path)

    if TYPEDEF_GRAPH_DB.exists() and not force:
        click.echo(f"⚠️  Graph database already exists at {TYPEDEF_GRAPH_DB}")
        if not click.confirm("Overwrite?"):
            click.echo("Aborted.")
            return

    ensure_typedef_dirs()

    click.echo(f"📥 Importing from {archive.name}...")

    # Extract tarball
    with tarfile.open(archive, "r:gz") as tar:
        # Read metadata first
        try:
            metadata_file = tar.extractfile("metadata.yaml")
            if metadata_file:
                metadata = yaml.safe_load(metadata_file.read())
                project_name = metadata.get("project_name", "unknown")
                click.echo(f"   Project: {project_name}")
                click.echo(f"   Exported: {metadata.get('exported_at', 'unknown')}")
        except KeyError:
            project_name = "unknown"

        click.echo()

        # Extract graph database
        click.echo("   Extracting graph database...")
        graph_member = tar.getmember("graph.db")
        tar.extract(graph_member, path=TYPEDEF_HOME)
        # Rename if needed
        extracted_db = TYPEDEF_HOME / "graph.db"
        if extracted_db != TYPEDEF_GRAPH_DB:
            shutil.move(extracted_db, TYPEDEF_GRAPH_DB)

        # Extract semantic cache
        cache_members = [m for m in tar.getmembers() if m.name.startswith("semantic_cache/")]
        if cache_members:
            click.echo("   Extracting semantic cache...")

            # Get dbt path from config if available
            if TYPEDEF_CONFIG.exists():
                with open(TYPEDEF_CONFIG) as f:
                    config = yaml.safe_load(f)
                dbt_path = Path(config.get("project", {}).get("dbt_path", "."))
            else:
                dbt_path = Path.cwd()

            cache_dest = dbt_path / SEMANTIC_CACHE_DIR
            cache_dest.mkdir(parents=True, exist_ok=True)

            for member in cache_members:
                tar.extract(member, path=dbt_path / ".lineage_workspace")

    click.echo()
    click.echo("✅ Import complete!")
    click.echo()
    click.echo("   The graph is ready. Start chatting with:")
    click.echo("   typedef chat")


# ============================================================================
# typedef config - Show/validate configuration
# ============================================================================

@main.group()
def config():
    """Show or validate configuration."""
    pass


@config.command("show")
def config_show():
    """Display current configuration."""
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    click.echo(f"📄 Configuration: {TYPEDEF_CONFIG}")
    click.echo("=" * 50)
    click.echo()

    with open(TYPEDEF_CONFIG) as f:
        content = f.read()

    # Mask sensitive values
    import re
    masked = re.sub(r'(private_key_path:\s*).+', r'\1***', content)
    masked = re.sub(r'(password:\s*).+', r'\1***', masked)
    masked = re.sub(r'(api_key:\s*).+', r'\1***', masked)

    click.echo(masked)


@config.command("validate")
def config_validate():
    """Validate the configuration file."""
    if not TYPEDEF_CONFIG.exists():
        click.echo("❌ No configuration found. Run 'typedef init' first.")
        sys.exit(1)

    click.echo(f"🔍 Validating {TYPEDEF_CONFIG}...")

    try:
        load_env_file()
        config = UnifiedConfig.from_yaml(TYPEDEF_CONFIG)

        click.echo()
        click.echo("✅ Configuration is valid!")
        click.echo()
        click.echo(f"   Lineage backend: {config.lineage.backend}")
        click.echo(f"   Data backend: {config.data.backend}")
        click.echo(f"   Tickets: {'enabled' if config.ticket.enabled else 'disabled'}")
        click.echo(f"   Reports: {'enabled' if config.reports.enabled else 'disabled'}")

    except Exception as e:
        click.echo()
        click.echo(f"❌ Configuration error: {e}")
        sys.exit(1)


@config.command("path")
def config_path():
    """Print the configuration file path."""
    click.echo(str(TYPEDEF_CONFIG))


# ============================================================================
# typedef reset - Reset all typedef data
# ============================================================================

@main.command("reset")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def reset(force: bool):
    """Reset typedef by deleting ~/.typedef directory.

    This removes all typedef data including:
    - Configuration file (config.yaml)
    - Graph database (graph.db)
    - Threads and conversation history
    - Reports and exports
    - All cached data

    Use with caution - this action cannot be undone.
    """
    if not TYPEDEF_HOME.exists():
        click.echo("ℹ️  Nothing to reset - ~/.typedef does not exist.")
        return

    # Show what will be deleted
    click.echo(f"⚠️  This will delete: {TYPEDEF_HOME}")
    click.echo()

    # List contents
    contents = list(TYPEDEF_HOME.iterdir())
    if contents:
        click.echo("   Contents to be deleted:")
        for item in contents:
            if item.is_dir():
                click.echo(f"   📁 {item.name}/")
            else:
                click.echo(f"   📄 {item.name}")
        click.echo()

    if not force:
        if not click.confirm("Are you sure you want to delete all typedef data?"):
            click.echo("Cancelled.")
            return

    # Delete the directory
    shutil.rmtree(TYPEDEF_HOME)
    click.echo()
    click.echo("✅ Reset complete. Run 'typedef init' to start fresh.")


# ============================================================================
# typedef dev-reset - Hidden dev command for quick dogfooding setup
# ============================================================================

@main.command("dev-reset", hidden=True)
@click.option("--cache-dir", type=click.Path(exists=True),
              help="Path to semantic cache dir to copy (default: .lineage_workspace/semantic_cache)")
def dev_reset(cache_dir: Optional[str]):
    """[INTERNAL] Quick reset for dogfooding - preserves semantic cache.

    This hidden command is for internal development use. It:
    1. Resets ~/.typedef
    2. Copies semantic cache from repo to ~/.typedef/semantic_cache/
    3. Prompts user to run typedef init

    The semantic cache in .lineage_workspace/semantic_cache/ is checked into
    the repo so team members can dogfood without re-running semantic analysis.

    Usage:
        cd /path/to/data-intelligence
        typedef dev-reset
        typedef init  # Configure your settings interactively
    """
    import shutil

    # Find repo root (look for .git directory)
    repo_root = Path.cwd()
    while repo_root != repo_root.parent:
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent
    else:
        repo_root = Path.cwd()  # Fallback to cwd if no .git found

    # Find semantic cache in repo
    if cache_dir:
        cache_source = Path(cache_dir)
    else:
        candidates = [
            repo_root / ".lineage_workspace" / "semantic_cache",
            Path.cwd() / ".lineage_workspace" / "semantic_cache",
        ]
        cache_source = None
        for candidate in candidates:
            if candidate.exists() and any(candidate.iterdir()):
                cache_source = candidate
                break

    click.echo("🔧 Dev reset")
    if cache_source:
        click.echo(f"   Cache source: {cache_source}")
    else:
        click.echo("   Cache source: (none found)")
    click.echo()

    # Step 1: Reset ~/.typedef
    if TYPEDEF_HOME.exists():
        click.echo(f"🗑️  Removing {TYPEDEF_HOME}...")
        shutil.rmtree(TYPEDEF_HOME)

    # Step 2: Create ~/.typedef directories
    ensure_typedef_dirs()

    # Step 3: Copy semantic cache from repo to ~/.typedef/semantic_cache/
    cache_dest = TYPEDEF_HOME / "semantic_cache"
    if cache_source:
        click.echo(f"📦 Copying semantic cache to {cache_dest}...")
        shutil.copytree(cache_source, cache_dest)
        click.echo("   ✅ Cache copied")
    else:
        cache_dest.mkdir(parents=True, exist_ok=True)
        click.echo("   ⚠️  No semantic cache found - will need to run semantic analysis")

    click.echo()
    click.echo("✅ Dev reset complete!")
    click.echo()
    click.echo("   Next steps:")
    click.echo("   1. typedef init      # Configure your settings")
    click.echo("   2. typedef sync      # Load graph (uses cached semantic analysis)")
    click.echo("   3. typedef chat      # Start chatting")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()

"""CLI-ready agents for PydanticAI.

This module exports agents that can be run via the CLI runner:
    uv run python -m lineage.agent.pydantic.cli_runner analyst
    uv run python -m lineage.agent.pydantic.cli_runner investigator
    uv run python -m lineage.agent.pydantic.cli_runner insights
    uv run python -m lineage.agent.pydantic.cli_runner copilot
    uv run python -m lineage.agent.pydantic.cli_runner reconciler

Configuration:
    By default, uses config.cli.yml in the project root.
    Override with UNIFIED_CONFIG environment variable:
        export UNIFIED_CONFIG=/path/to/config.yml

Usage Examples:
    # Run analyst agent interactively
    uv run python -m lineage.agent.pydantic.cli_runner analyst

    # Ask a single question
    uv run python -m lineage.agent.pydantic.cli_runner analyst "What semantic views are available?"

    # Run investigator agent (reactive troubleshooting)
    uv run python -m lineage.agent.pydantic.cli_runner investigator "Why is ARR wrong?"

    # Run insights agent (architecture explanation)
    uv run python -m lineage.agent.pydantic.cli_runner insights "Explain this model to me"

    # Run data engineer copilot (interactive, full file/git access)
    uv run python -m lineage.agent.pydantic.cli_runner copilot "Add a new dimension to fct_revenue"

    # Run data engineer reconciler (autonomous ticket processing)
    uv run python -m lineage.agent.pydantic.cli_runner reconciler "Work on ticket TICKET-123"

Note:
    The agents are initialized once when the module is imported. User context defaults to:
    - user_id: "cli_user@example.com"
    - org_id: "cli_org"

    Override with environment variables:
    - CLI_USER_ID: Set user ID for memory context
    - CLI_ORG_ID: Set org ID for memory context
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from pathlib import Path

from ag_ui.core import RunAgentInput

from lineage.agent.pydantic.orchestrator import (
    create_analyst_orchestrator,
    create_data_engineer_copilot_orchestrator,
    create_data_engineer_reconciler_orchestrator,
    create_data_insights_orchestrator,
    create_data_investigator_orchestrator,
)
from lineage.agent.pydantic.types import FileSystemConfig
from lineage.backends.config import UnifiedConfig
from lineage.backends.data_query.factory import create_data_backend_for_cli
from lineage.backends.lineage.factory import create_storage_for_cli
from lineage.backends.memory.factory import create_memory_backend
from lineage.backends.tickets.factory import create_ticket_backend_from_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration Loading
# ============================================================================


def _find_config_path() -> Path:
    """Find config file from environment or default locations.

    Priority:
    1. UNIFIED_CONFIG environment variable
    2. config.cli.yml in module root (preferred for CLI agents)
    3. config.yml in current directory
    4. config.example.yml in current directory
    5. config.yml in module parent directory
    6. config.example.yml in module parent directory

    Returns:
        Path to config file

    Raises:
        FileNotFoundError: If no config file is found
    """
    # Check environment variable
    config_env = os.getenv("UNIFIED_CONFIG")
    if config_env:
        config_path = Path(config_env)
        if config_path.exists():
            return config_path
        logger.warning(f"UNIFIED_CONFIG points to non-existent file: {config_path}")

    # Check module parent directory (typedef_data_intelligence root) for CLI-specific config first
    module_root = Path(__file__).parent.parent.parent.parent.parent
    cli_config = module_root / "config.cli.yml"
    if cli_config.exists():
        return cli_config

    # Check current directory
    for name in ["config.yml", "config.example.yml"]:
        config_path = Path.cwd() / name
        if config_path.exists():
            return config_path

    # Check module parent directory for general configs
    for name in ["config.yml", "config.example.yml"]:
        config_path = module_root / name
        if config_path.exists():
            return config_path

    raise FileNotFoundError(
        "No config file found. Set UNIFIED_CONFIG or create config.cli.yml in project root."
    )


def _create_cli_input_data() -> RunAgentInput:
    """Create a mock RunAgentInput for CLI usage.

    CLI agents don't run within the full AG-UI protocol, so we create
    minimal input data with generated thread/run IDs.
    """
    return RunAgentInput(
        thread_id=f"cli-thread-{uuid.uuid4().hex[:8]}",
        run_id=f"cli-run-{uuid.uuid4().hex[:8]}",
        state={},
        messages=[],
        tools=[],
        context=[],
        forwarded_props={},
    )


# ============================================================================
# Initialize Backends and Agents
# ============================================================================

logger.info("=" * 60)
logger.info("Initializing CLI Agents")
logger.info("=" * 60)

# Find and load config
try:
    config_path = _find_config_path()
    logger.info(f"Loading config from: {config_path}")
    cfg = UnifiedConfig.from_yaml(config_path)
except FileNotFoundError as e:
    logger.error(f"❌ {e}")
    logger.error("Set UNIFIED_CONFIG environment variable or create config.yml")
    sys.exit(1)
except ValueError as e:
    logger.error(f"❌ Invalid config: {e}")
    sys.exit(1)

logger.info(f"✅ Lineage backend: {cfg.lineage.backend}")
logger.info(f"✅ Data backend: {cfg.data.backend}")

# Initialize backends
lineage_backend = create_storage_for_cli(cfg.lineage, read_only=True)
data_backend = create_data_backend_for_cli(cfg.data, read_only=True)

# Initialize memory backend (optional)
memory_backend = None
if cfg.memory.enabled:
    memory_backend = create_memory_backend(cfg.memory)
    if memory_backend:
        logger.info("✅ Memory backend initialized")
    else:
        logger.warning("⚠️  Memory backend initialization failed")
else:
    logger.info("ℹ️  Memory backend disabled")

# Initialize ticket storage (optional)
ticket_storage = None
data_engineer_ticket_storage = None
if cfg.ticket.enabled:
    logger.info(f"🎫 Initializing ticket storage: {cfg.ticket.backend}")
    ticket_storage = create_ticket_backend_from_config(cfg.ticket, role="analyst")
    if ticket_storage:
        logger.info(f"✅ Analyst Ticket storage initialized: {cfg.ticket.backend}")
    else:
        logger.warning("⚠️  Analyst Ticket storage initialization failed (graceful degradation)")
    
    data_engineer_ticket_storage = create_ticket_backend_from_config(cfg.ticket, role="data_engineer")
    if data_engineer_ticket_storage:
        logger.info(f"✅ Data Engineer Ticket storage initialized: {cfg.ticket.backend}")
    else:
        logger.warning("⚠️  Data Engineer Ticket storage initialization failed (graceful degradation)")
else:
    logger.info("ℹ️  Ticket storage disabled (set ticket.enabled=true to enable)")

# User context from environment or defaults
cli_user_id = os.getenv("CLI_USER_ID", "cli_user@example.com")
cli_org_id = os.getenv("CLI_ORG_ID", "cli_org")

# Analyst Agent
analyst_agent, analyst_deps = create_analyst_orchestrator(
    lineage=lineage_backend,
    input_data=_create_cli_input_data(),
    data_backend=data_backend,
    memory_backend=memory_backend,
    ticket_storage=ticket_storage,
    model=cfg.agent.analyst.model,
)
analyst_deps.user_id = cli_user_id
analyst_deps.org_id = cli_org_id

logger.info(f"✅ Analyst agent ready (user={analyst_deps.user_id}, org={analyst_deps.org_id})")

# Data Investigator Agent (reactive troubleshooting)
investigator_agent, investigator_deps = create_data_investigator_orchestrator(
    lineage=lineage_backend,
    input_data=_create_cli_input_data(),
    data_backend=data_backend,
    memory_backend=memory_backend,
    ticket_storage=data_engineer_ticket_storage or ticket_storage,
    model=cfg.agent.investigator.model,
)
investigator_deps.user_id = cli_user_id
investigator_deps.org_id = cli_org_id

logger.info(f"✅ Investigator agent ready (user={investigator_deps.user_id}, org={investigator_deps.org_id})")

# Data Insights Agent (architecture explanation)
insights_agent, insights_deps = create_data_insights_orchestrator(
    lineage=lineage_backend,
    input_data=_create_cli_input_data(),
    data_backend=data_backend,
    memory_backend=memory_backend,
    ticket_storage=data_engineer_ticket_storage or ticket_storage,
    model=cfg.agent.insights.model,
)
insights_deps.user_id = cli_user_id
insights_deps.org_id = cli_org_id

logger.info(f"✅ Insights agent ready (user={insights_deps.user_id}, org={insights_deps.org_id})")

# ============================================================================
# Copilot and Reconciler Agents (require git config)
# ============================================================================

copilot_agent = None
copilot_deps = None
reconciler_agent = None
reconciler_deps = None

# Get git config from active project (env var takes precedence over default)
active_project = os.getenv("TYPEDEF_ACTIVE_PROJECT") or cfg.default_project
git_config = None
if active_project and cfg.projects:
    try:
        git_config = cfg.get_project_git_config(active_project)
    except KeyError:
        logger.warning(f"⚠️  Project '{active_project}' not found in configuration")

if git_config and git_config.enabled and git_config.working_directory:
    logger.info("")
    logger.info(f"Initializing file/git-enabled agents for project: {active_project}...")

    # Create filesystem config from git working directory
    filesystem_config = FileSystemConfig(
        working_directory=git_config.working_directory,
        read_only=False,
    )

    # Data Engineer Copilot (interactive mode with full file/git access)
    copilot_agent, copilot_deps = create_data_engineer_copilot_orchestrator(
        lineage=lineage_backend,
        input_data=_create_cli_input_data(),
        filesystem_config=filesystem_config,
        git_config=git_config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=data_engineer_ticket_storage,
        model=cfg.agent.data_engineer.model,
    )
    copilot_deps.user_id = cli_user_id
    copilot_deps.org_id = cli_org_id

    logger.info(f"✅ Copilot agent ready (project={active_project}, working_dir={git_config.working_directory})")

    # Data Engineer Reconciler (autonomous ticket processing)
    reconciler_agent, reconciler_deps = create_data_engineer_reconciler_orchestrator(
        lineage=lineage_backend,
        input_data=_create_cli_input_data(),
        filesystem_config=filesystem_config,
        git_config=git_config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=data_engineer_ticket_storage,
        model=cfg.agent.data_engineer.model,
    )
    reconciler_deps.user_id = cli_user_id
    reconciler_deps.org_id = cli_org_id

    logger.info(f"✅ Reconciler agent ready (project={active_project}, working_dir={git_config.working_directory})")
else:
    logger.info("")
    logger.info("ℹ️  Git not enabled - copilot/reconciler agents not available")
    if cfg.default_project and cfg.projects:
        logger.info(f"   Configure git in the '{cfg.default_project}' project section to enable these agents")
    else:
        logger.info("   Configure a default project with git settings to enable these agents")

logger.info("")
logger.info("=" * 60)
logger.info("All CLI agents ready!")
logger.info("")
logger.info("Usage:")
logger.info('  uv run python -m lineage.agent.pydantic.cli_runner analyst "What views are available?"')
logger.info('  uv run python -m lineage.agent.pydantic.cli_runner investigator "Why is ARR wrong?"')
logger.info('  uv run python -m lineage.agent.pydantic.cli_runner insights "Explain this model"')
if copilot_agent:
    logger.info('  uv run python -m lineage.agent.pydantic.cli_runner copilot "Add dimension to fct_revenue"')
    logger.info('  uv run python -m lineage.agent.pydantic.cli_runner reconciler "Work on ticket TICKET-123"')
logger.info("=" * 60)

# ============================================================================
# Export agents for clai discovery
# ============================================================================

# clai will look for these exported names
analyst = analyst_agent
investigator = investigator_agent
insights = insights_agent
copilot = copilot_agent
reconciler = reconciler_agent

# Also export deps for programmatic access
__all__ = [
    "analyst",
    "investigator",
    "insights",
    "copilot",
    "reconciler",
    "analyst_deps",
    "investigator_deps",
    "insights_deps",
    "copilot_deps",
    "reconciler_deps",
]

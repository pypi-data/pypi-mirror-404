"""Application entry point for the WebUI/OpenLineage backend."""
import logging
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logfire
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from lineage.backends.config import GitConfig, UnifiedConfig
from lineage.backends.data_query import DataQueryBackend
from lineage.backends.data_query.factory import create_data_backend_for_cli
from lineage.backends.lineage import LineageStorage
from lineage.backends.lineage.factory import create_storage_for_cli
from lineage.backends.memory import MemoryStorage
from lineage.backends.memory.factory import create_memory_backend
from lineage.backends.reports import ReportsBackend
from lineage.backends.reports.factory import create_reports_backend
from lineage.backends.threads import ThreadsBackend, create_threads_backend
from lineage.backends.tickets import TicketStorage
from lineage.backends.tickets.factory import create_ticket_backend_from_config
from lineage.ingest.openlineage.loader import NamespaceResolver, OpenLineageLoader
from lineage.utils.env import load_env_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# User Context Models
# ============================================================================


@dataclass
class UserContext:
    """User context extracted from request headers.

    This provides proper type safety for user identity across the application.
    """

    user_id: str
    org_id: str


def get_user_context(request: Request) -> UserContext:
    """FastAPI dependency to extract user context from request.

    This properly typed dependency replaces getattr() calls.

    Returns:
        UserContext with user_id and org_id

    Note:
        Values are set by the extract_user_context middleware.
    """
    return UserContext(
        user_id=request.state.user_id,
        org_id=request.state.org_id,
    )


# ============================================================================
# Application State
# ============================================================================


@dataclass
class AppState:
    """Application-wide state container.

    Encapsulates all application state including backends, orchestrators,
    and configuration. This provides type-safe access to state and eliminates
    global variables.

    Stored in app.state.app_state and accessed via dependency injection.
    """

    # Configuration
    config: UnifiedConfig

    #Loaders
    openlineage_loader: OpenLineageLoader

    # Backends
    lineage: LineageStorage
    data_backend: DataQueryBackend
    memory_backend: Optional[MemoryStorage] = None
    ticket_storage: Optional[TicketStorage] = None  # Analyst role
    de_ticket_storage: Optional[TicketStorage] = None  # Data Engineer role (for daemon/investigator/reconciler)
    reports_backend: Optional[ReportsBackend] = None
    threads_backend: Optional[ThreadsBackend] = None
    git_config: Optional[GitConfig] = None  # Per-project git configuration


# ============================================================================
# Middleware for Request Logging and User Context Extraction
# ============================================================================




@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown.

    This replaces the deprecated @app.on_event("startup") and @app.on_event("shutdown")
    patterns with the modern lifespan approach.

    Yields control to the application after initialization, then performs cleanup
    on shutdown.
    """
    # Configure logfire once at startup (before importing orchestrator which uses it)
    # This ensures span context propagates correctly through asyncio.
    logfire_token = os.getenv('LOGFIRE_TOKEN')
    if logfire_token:
        logfire.configure(token=logfire_token, console=False)

    # Startup: Initialize all state
    state = initialize_app_state()
    app.state.app_state = state

    logger.info("✅ Application ready to serve requests")

    yield  # Application runs here

    # Shutdown: Cleanup resources
    logger.info("🔄 Shutting down gracefully...")
    # await state.memory_backend.close()
    # state.ticket_storage.close()
    
    logger.info("✅ Shutdown complete")


def get_app_state(request: Request) -> AppState:
    """FastAPI dependency to get application state.

    Provides type-safe access to all application state including backends
    and orchestrators.

    Args:
        request: FastAPI request object

    Returns:
        AppState with all initialized backends and orchestrators

    Example:
        ```python
        @app.post("/agents/analyst")
        async def run_analyst(state: !State = Depends(get_app_state)):
            return await handle_request(state.analyst_orchestrator, ...)
        ```
    """
    return request.app.state.app_state


# ============================================================================
# State Initialization
# ============================================================================


def initialize_app_state() -> AppState:
    """Initialize all application state including backends and orchestrators.

    This function loads configuration, initializes all backends (lineage, data,
    memory, ticket), and creates all orchestrators with their dependencies.

    Returns:
        Fully initialized AppState

    Raises:
        SystemExit: If configuration is invalid or required backends fail to initialize
    """
    load_env_file()
    logger.info("🚀 Starting PydanticAI Native Backend (Simplified 2-Level Architecture)")
    logger.info("=" * 60)

    # Load unified config from environment
    config_path_str = os.getenv("UNIFIED_CONFIG")
    if not config_path_str:
        logger.error("❌ UNIFIED_CONFIG environment variable not set")
        logger.error("   Set it to the path of your config.yml file")
        logger.error("   Example: export UNIFIED_CONFIG=/path/to/config.yml")
        sys.exit(1)

    config_path = Path(config_path_str)
    if not config_path.exists():
        logger.error(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    logger.info(f"📄 Loading config from: {config_path}")

    try:
        cfg = UnifiedConfig.from_yaml(config_path)
    except (ValueError, FileNotFoundError) as e:
        logger.error(f"❌ Failed to load config: {e}")
        sys.exit(1)

    logger.info(f"✅ Lineage backend: {cfg.lineage.backend}")
    logger.info(f"✅ Data backend: {cfg.data.backend}")
    logger.info(f"✅ Agent model: {cfg.agent.analyst.model} for analyst and {cfg.agent.data_engineer.model} for data engineer")

    # Check for active project/graph
    graph_name = os.getenv("TYPEDEF_GRAPH_NAME")
    if graph_name:
        logger.info(f"📁 Active project graph: {graph_name}")

    # Initialize lineage backend
    lineage = create_storage_for_cli(cfg.lineage, read_only=True)
    lineage_writeable = create_storage_for_cli(cfg.lineage, read_only=False)

    # Set active graph if specified
    if graph_name:
        lineage.set_active_graph(graph_name)
        lineage_writeable.set_active_graph(graph_name)

    # Initialize data backend with per-project overrides if applicable
    active_project = os.getenv("TYPEDEF_ACTIVE_PROJECT") or cfg.default_project
    if active_project and cfg.projects and active_project in cfg.projects:
        logger.info(f"📁 Applying per-project data overrides for: {active_project}")
        data_config = cfg.get_project_data_config(active_project)
    else:
        data_config = cfg.data
    data_backend = create_data_backend_for_cli(data_config, read_only=True)

    # Get per-project git config if active project specified
    git_config = None
    if active_project and cfg.projects and active_project in cfg.projects:
        git_config = cfg.get_project_git_config(active_project)
        if git_config and git_config.enabled:
            logger.info(f"📁 Git configuration loaded for project: {active_project}")

    # Initialize memory backend (optional)
    memory_backend: Optional[MemoryStorage] = None
    if cfg.memory and cfg.memory.enabled:
        logger.info(f"📝 Initializing memory backend: {cfg.memory.backend}")
        memory_backend = create_memory_backend(cfg.memory)
        if memory_backend:
            logger.info("✅ Memory backend initialized")
        else:
            logger.warning("⚠️  Memory backend initialization failed (graceful degradation)")
    else:
        logger.info("ℹ️  Memory backend disabled (add memory config section to enable)")

    # Initialize ticket storage (optional)
    # Create separate ticket storages for analyst and data engineer roles
    # This allows proper attribution when adding comments/updates to Linear tickets
    ticket_storage: Optional[TicketStorage] = None
    de_ticket_storage: Optional[TicketStorage] = None
    if cfg.ticket.enabled:
        logger.info(f"🎫 Initializing ticket storage: {cfg.ticket.backend}")
        # Analyst ticket storage (for analyst agent)
        ticket_storage = create_ticket_backend_from_config(
            config=cfg.ticket,
            role="analyst",
        )
        if ticket_storage:
            logger.info("✅ Analyst Ticket storage initialized")
        else:
            logger.warning("⚠️  Analyst Ticket storage initialization failed (graceful degradation)")

        # Data Engineer ticket storage (for investigator/reconciler/copilot/daemon agents)
        de_ticket_storage = create_ticket_backend_from_config(
            config=cfg.ticket,
            role="data_engineer",
        )
        if de_ticket_storage:
            logger.info("✅ Data Engineer Ticket storage initialized")
        else:
            logger.warning("⚠️  Data Engineer Ticket storage initialization failed (graceful degradation)")
    else:
        logger.info("ℹ️  Ticket storage disabled (set ticket.enabled=true to enable)")

    # Initialize reports backend (always enabled)
    logger.info("📊 Initializing reports backend")
    reports_backend = create_reports_backend(cfg.reports)
    if reports_backend:
        logger.info("✅ Reports backend initialized (path=./reports)")
    else:
        logger.warning("⚠️  Reports backend initialization failed (graceful degradation)")

    # Initialize threads backend for conversation memory
    logger.info("🧵 Initializing threads backend")
    threads_backend = None
    if cfg.threads.enabled:
        threads_backend = create_threads_backend(cfg.threads)
        if threads_backend:
            logger.info(f"✅ Threads backend initialized (cfg={cfg.threads})")
        else:
            logger.warning("⚠️  Threads backend initialization failed (graceful degradation)")
    else:
        logger.info("ℹ️  Threads backend disabled")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Endpoints:")
    logger.info("  - POST /api/v1/lineage     → OpenLineage Collector")
    logger.info("  - POST /agents/analyst     → Analyst (metadata, data, reports)")
    logger.info("  - POST /agents/quality     → Data Quality (troubleshooting)")
    logger.info("  - POST /agents/engineer    → Data Engineering (dbt, SQL)")
    logger.info("  - GET  /health             → Health check")
    logger.info("  - GET  /reports            → List saved reports")
    logger.info("  - GET  /reports/{report_id}         → View report by ID")
    logger.info("  - GET  /reports/{report_id}/export  → Download HTML export")
    logger.info("=" * 60)

    # Create and return app state
    return AppState(
        config=cfg,
        lineage=lineage,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        de_ticket_storage=de_ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        git_config=git_config,
        openlineage_loader=OpenLineageLoader(storage=lineage_writeable, resolver=NamespaceResolver()),
    )

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Lineage WebUI - PydanticAI Native Backend",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {request.method} {request.url.path} - {response.status_code}")
    return response


@app.middleware("http")
async def extract_user_context(request: Request, call_next):
    """Extract user and organization context from HTTP headers.

    Looks for:
    - X-User-Id: Unique user identifier
    - X-Org-Id: Organization identifier

    For testing/development, defaults to:
    - user_id: "test_user@example.com"
    - org_id: "test_org"

    Override by setting headers from frontend or environment variables:
    - DEFAULT_USER_ID: Default user ID if header not present
    - DEFAULT_ORG_ID: Default org ID if header not present

    Stores context in request.state for use in agent endpoints.
    """
    # Use environment variables for defaults (useful for different test setups)
    default_user_id = os.getenv("DEFAULT_USER_ID", "test_user@example.com")
    default_org_id = os.getenv("DEFAULT_ORG_ID", "test_org")

    # Extract from headers, fall back to defaults
    user_id = request.headers.get("X-User-Id", default_user_id)
    org_id = request.headers.get("X-Org-Id", default_org_id)

    # Store in request state
    request.state.user_id = user_id
    request.state.org_id = org_id

    # Log user context for debugging
    logger.info(f"  User context: user_id={user_id}, org_id={org_id}")

    return await call_next(request)


from lineage.api import collector, pydantic  # noqa: E402, F401

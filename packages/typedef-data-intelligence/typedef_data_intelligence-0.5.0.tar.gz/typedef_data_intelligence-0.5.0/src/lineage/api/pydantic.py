"""Pydantic AI agent API endpoints.

This module provides FastAPI endpoints for running Pydantic AI agents
(analyst, data quality, data engineering orchestrators) and serving reports.
"""
import logging
import os
from pathlib import Path

from ag_ui.core import RunAgentInput
from fastapi import Depends, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from lineage.agent.pydantic.ag_ui_handler import handle_ag_ui_request_with_thinking
from lineage.agent.pydantic.orchestrator import (
    create_analyst_orchestrator,
    create_data_engineer_copilot_orchestrator,
    create_data_engineer_reconciler_orchestrator,
    create_data_insights_orchestrator,
    create_data_investigator_orchestrator,
    create_data_quality_orchestrator,
)
from lineage.agent.pydantic.summary import (
    generate_and_save_run_summary,
)
from lineage.agent.pydantic.tools.presentation import generate_standalone_html
from lineage.agent.pydantic.types import AgentDeps, FileSystemConfig
from lineage.api.app import AppState, UserContext, app, get_app_state, get_user_context
from pydantic_ai import AgentRunResult
from pydantic_ai.ag_ui import OnCompleteFunc

# Configure logging with more visible format

logger = logging.getLogger(__name__)
# Enable debug logging for AG-UI handler to track thinking block extraction
logging.getLogger("lineage.agent.pydantic.ag_ui_handler").setLevel(logging.DEBUG)


def _ensure_dbt_profiles_env(state: AppState) -> None:
    """Ensure DBT_PROFILES_DIR is set for agent dbt tooling."""
    if os.environ.get("DBT_PROFILES_DIR"):
        return

    active_project = os.getenv("TYPEDEF_ACTIVE_PROJECT") or state.config.default_project
    if not active_project or not state.config.projects:
        return

    project_cfg = state.config.projects.get(active_project)
    if not project_cfg:
        return

    profiles_dir = project_cfg.profiles_dir or (Path.home() / ".typedef" / "profiles" / active_project)
    os.environ["DBT_PROFILES_DIR"] = str(Path(profiles_dir).expanduser().resolve())


# ============================================================================
# Agent Endpoint Wrapper (Thread Memory Support)
# ============================================================================


def create_save_summary_async(
    thread_id: str,
    run_id: str,
    deps: AgentDeps,
) -> OnCompleteFunc:
    """Create a background task to generate and save run summary."""
    async def save_summary_async(run_result: AgentRunResult):
        """Background task to generate and save run summary.

        This is called after the response is sent, so we can safely await
        the summary generation without blocking the response.
        """
        if deps.threads_backend is None:
            return

        try:
            run_messages = run_result.new_messages()
            await generate_and_save_run_summary(
                run_messages, thread_id, run_id, deps.threads_backend
            )
            logger.info(
                f"✅ [Background] Saved run summary for thread {thread_id}, run {run_id}"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to save run summary for thread {thread_id}, run {run_id}: {e}",
                exc_info=True,
            )

    return save_summary_async


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/health")
async def health_check(
    request: Request,
    state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """Health check endpoint.

    Returns the health status of the application and all orchestrators.
    Uses app.state for type-safe access to orchestrators.
    """
    return {
        "status": "healthy",
        "orchestrators": {
            "analyst": "ready",
            "quality": "ready",
            "engineering": "ready",
        },
        "backends": {
            "lineage": state.config.lineage.backend,
            "data": state.config.data.backend,
            "memory": "enabled" if state.memory_backend else "disabled",
            "tickets": "enabled" if state.ticket_storage else "disabled",
            "reports": "enabled" if state.reports_backend else "disabled",
            "threads": "enabled" if state.threads_backend else "disabled",
        },
    }


@app.post("/agents/analyst")
async def run_analyst(
    request: Request,
    user_context: UserContext = Depends(get_user_context), #noqa: B008 expected for fastapi
    state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """AG-UI protocol endpoint for Analyst orchestrator with thread memory.

    This endpoint:
    1. Parses AG-UI request to extract thread_id and run_id
    2. Loads thread context from previous runs
    3. Creates orchestrator with thread context injected into prompt
    4. Streams response to client
    5. Async saves run summary to thread store (fire-and-forget)

    Uses dependency injection for type-safe access to state.
    Creates request-specific dependencies with user context.
    """
    # Parse AG-UI request body to extract thread_id and run_id
    body_bytes = await request.body()
    input_data = RunAgentInput.model_validate_json(body_bytes)
    _ensure_dbt_profiles_env(state)

    thread_id = input_data.thread_id
    run_id = input_data.run_id

    # Load thread context from backend
    thread_context = None
    if state.threads_backend:
        thread_context = state.threads_backend.get_or_create_thread(thread_id)

    # Create orchestrator with thread context
    analyst_orchestrator, analyst_deps = create_analyst_orchestrator(
        input_data=input_data,
        lineage=state.lineage,
        data_backend=state.data_backend,
        memory_backend=state.memory_backend,
        ticket_storage=state.ticket_storage,
        reports_backend=state.reports_backend,
        threads_backend=state.threads_backend,
        model=state.config.agent.analyst.model,
        thread_context=thread_context,
    )

    analyst_deps.user_id = user_context.user_id
    analyst_deps.org_id = user_context.org_id

    # Recreate request with body for handle_ag_ui_request
    async def receive():
        return {"type": "http.request", "body": body_bytes}

    new_request = Request(
        scope=request.scope,
        receive=receive,
    )
    summary_func = create_save_summary_async(
        thread_id=thread_id,
        run_id=run_id,
        deps=analyst_deps,
    )
    return await handle_ag_ui_request_with_thinking(
        agent=analyst_orchestrator,
        request=new_request,
        deps=analyst_deps,
        on_complete=summary_func,
    )


@app.post("/agents/quality")
async def run_quality(
    request: Request,
    user_context: UserContext = Depends(get_user_context), #noqa: B008 expected for fastapi
    state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """AG-UI protocol endpoint for Data Quality orchestrator with thread memory.

    This endpoint handles data quality queries: troubleshooting,
    error diagnosis, and operational monitoring.

    Uses dependency injection for type-safe access to state.
    Creates request-specific dependencies with user context.
    """
    # Parse AG-UI request body to extract thread_id and run_id
    body_bytes = await request.body()
    input_data = RunAgentInput.model_validate_json(body_bytes)
    _ensure_dbt_profiles_env(state)

    thread_id = input_data.thread_id
    run_id = input_data.run_id

    logger.info(f"📋 Quality request: thread={thread_id}, run={run_id}")

    # Load thread context from backend
    thread_context = None
    if state.threads_backend:
        thread_context = state.threads_backend.get_or_create_thread(thread_id)
        logger.info(
            f"🧵 Loaded thread context with {len(thread_context.runs)} previous runs"
        )

    quality_orchestrator, quality_deps = create_data_quality_orchestrator(
        input_data=input_data,
        lineage=state.lineage,
        data_backend=state.data_backend,
        memory_backend=state.memory_backend,
        ticket_storage=state.ticket_storage,
        reports_backend=state.reports_backend,
        threads_backend=state.threads_backend,
        model=state.config.agent.quality.model,
        thread_context=thread_context,
    )

    quality_deps.user_id = user_context.user_id
    quality_deps.org_id = user_context.org_id

    # Recreate request with body for handle_ag_ui_request
    async def receive():
        return {"type": "http.request", "body": body_bytes}

    new_request = Request(
        scope=request.scope,
        receive=receive,
    )
    summary_func = create_save_summary_async(
        thread_id=thread_id,
        run_id=run_id,
        deps=quality_deps,
    )
    return await handle_ag_ui_request_with_thinking(
        agent=quality_orchestrator,
        request=new_request,
        deps=quality_deps,
        on_complete=summary_func,
    )


@app.post("/agents/investigator")
async def run_investigator(
    request: Request,
    user_context: UserContext = Depends(get_user_context), #noqa: B008 expected for fastapi
    state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """AG-UI protocol endpoint for Data Investigator orchestrator.

    This endpoint handles reactive troubleshooting: user brings a problem
    like "Why is ARR wrong?" and the agent investigates using lineage-first approach.
    """
    body_bytes = await request.body()
    input_data = RunAgentInput.model_validate_json(body_bytes)
    _ensure_dbt_profiles_env(state)

    thread_id = input_data.thread_id
    run_id = input_data.run_id

    logger.info(f"🔍 Investigator request: thread={thread_id}, run={run_id}")

    thread_context = None
    if state.threads_backend:
        thread_context = state.threads_backend.get_or_create_thread(thread_id)

    investigator_orchestrator, investigator_deps = create_data_investigator_orchestrator(
        input_data=input_data,
        lineage=state.lineage,
        data_backend=state.data_backend,
        memory_backend=state.memory_backend,
        ticket_storage=state.de_ticket_storage or state.ticket_storage,  # Use DE token for ticket comments
        reports_backend=state.reports_backend,
        threads_backend=state.threads_backend,
        model=state.config.agent.investigator.model,
        thread_context=thread_context,
    )

    investigator_deps.user_id = user_context.user_id
    investigator_deps.org_id = user_context.org_id

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    new_request = Request(
        scope=request.scope,
        receive=receive,
    )
    summary_func = create_save_summary_async(
        thread_id=thread_id,
        run_id=run_id,
        deps=investigator_deps,
    )
    return await handle_ag_ui_request_with_thinking(
        agent=investigator_orchestrator,
        request=new_request,
        deps=investigator_deps,
        on_complete=summary_func,
    )


@app.post("/agents/insights")
async def run_insights(
    request: Request,
    user_context: UserContext = Depends(get_user_context), #noqa: B008 expected for fastapi
    state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """AG-UI protocol endpoint for Data Insights orchestrator.

    This endpoint handles architecture explanation and pattern surfacing:
    "Explain this model", "How do these tables join?", "What measures are available?"
    """
    body_bytes = await request.body()
    input_data = RunAgentInput.model_validate_json(body_bytes)
    _ensure_dbt_profiles_env(state)

    thread_id = input_data.thread_id
    run_id = input_data.run_id

    logger.info(f"💡 Insights request: thread={thread_id}, run={run_id}")

    thread_context = None
    if state.threads_backend:
        thread_context = state.threads_backend.get_or_create_thread(thread_id)

    insights_orchestrator, insights_deps = create_data_insights_orchestrator(
        input_data=input_data,
        lineage=state.lineage,
        data_backend=state.data_backend,
        memory_backend=state.memory_backend,
        ticket_storage=state.de_ticket_storage or state.ticket_storage,  # Use DE token for ticket comments
        reports_backend=state.reports_backend,
        threads_backend=state.threads_backend,
        model=state.config.agent.insights.model,
        thread_context=thread_context,
    )

    insights_deps.user_id = user_context.user_id
    insights_deps.org_id = user_context.org_id

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    new_request = Request(
        scope=request.scope,
        receive=receive,
    )
    summary_func = create_save_summary_async(
        thread_id=thread_id,
        run_id=run_id,
        deps=insights_deps,
    )
    return await handle_ag_ui_request_with_thinking(
        agent=insights_orchestrator,
        request=new_request,
        deps=insights_deps,
        on_complete=summary_func,
    )


@app.post("/agents/copilot")
async def run_copilot(
    request: Request,
    user_context: UserContext = Depends(get_user_context), #noqa: B008 expected for fastapi
    state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """AG-UI protocol endpoint for Data Engineer Copilot orchestrator.

    This endpoint provides interactive data engineering capabilities
    with file system and git access.
    """
    # Parse AG-UI request body to extract thread_id and run_id
    body_bytes = await request.body()
    input_data = RunAgentInput.model_validate_json(body_bytes)
    _ensure_dbt_profiles_env(state)

    thread_id = input_data.thread_id
    run_id = input_data.run_id

    logger.info(f"👨‍💻 Copilot request: thread={thread_id}, run={run_id}")

    # Load thread context from backend
    thread_context = None
    if state.threads_backend:
        thread_context = state.threads_backend.get_or_create_thread(thread_id)

    # Create filesystem config - prefer per-project git config when enabled, fall back to env var / cwd
    if state.git_config and state.git_config.enabled and state.git_config.working_directory:
        working_dir = state.git_config.working_directory
    else:
        working_dir = Path(os.environ.get("GIT_WORKING_DIR", os.getcwd()))
    filesystem_config = FileSystemConfig(
        working_directory=working_dir,
        read_only=False,
    )

    copilot_orchestrator, copilot_deps = create_data_engineer_copilot_orchestrator(
        input_data=input_data,
        lineage=state.lineage,
        filesystem_config=filesystem_config,
        git_config=state.git_config,
        data_backend=state.data_backend,
        memory_backend=state.memory_backend,
        ticket_storage=state.de_ticket_storage or state.ticket_storage,  # Use DE token for ticket comments
        reports_backend=state.reports_backend,
        threads_backend=state.threads_backend,
        model=state.config.agent.data_engineer.model,
        thread_context=thread_context,
    )

    copilot_deps.user_id = user_context.user_id
    copilot_deps.org_id = user_context.org_id

    # Recreate request with body for handle_ag_ui_request
    async def receive():
        return {"type": "http.request", "body": body_bytes}

    new_request = Request(
        scope=request.scope,
        receive=receive,
    )
    summary_func = create_save_summary_async(
        thread_id=thread_id,
        run_id=run_id,
        deps=copilot_deps,
    )
    return await handle_ag_ui_request_with_thinking(
        agent=copilot_orchestrator,
        request=new_request,
        deps=copilot_deps,
        on_complete=summary_func,
    )


@app.post("/agents/reconciler")
async def run_reconciler(
    request: Request,
    user_context: UserContext = Depends(get_user_context), #noqa: B008 expected for fastapi
    state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """AG-UI protocol endpoint for Data Engineer Reconciler orchestrator.

    This endpoint provides autonomous ticket resolution capabilities.
    """
    # Parse AG-UI request body to extract thread_id and run_id
    body_bytes = await request.body()
    input_data = RunAgentInput.model_validate_json(body_bytes)
    _ensure_dbt_profiles_env(state)

    thread_id = input_data.thread_id
    run_id = input_data.run_id

    logger.info(f"🤖 Reconciler request: thread={thread_id}, run={run_id}")

    # Load thread context from backend
    thread_context = None
    if state.threads_backend:
        thread_context = state.threads_backend.get_or_create_thread(thread_id)

    # Create filesystem config - prefer per-project git config when enabled, fall back to env var / cwd
    if state.git_config and state.git_config.enabled and state.git_config.working_directory:
        working_dir = state.git_config.working_directory
    else:
        working_dir = Path(os.environ.get("GIT_WORKING_DIR", os.getcwd()))
    filesystem_config = FileSystemConfig(
        working_directory=working_dir,
        read_only=False,
    )

    reconciler_orchestrator, reconciler_deps = create_data_engineer_reconciler_orchestrator(
        input_data=input_data,
        lineage=state.lineage,
        filesystem_config=filesystem_config,
        git_config=state.git_config,
        data_backend=state.data_backend,
        memory_backend=state.memory_backend,
        ticket_storage=state.de_ticket_storage or state.ticket_storage,  # Use DE token for ticket comments
        reports_backend=state.reports_backend,
        threads_backend=state.threads_backend,
        model=state.config.agent.data_engineer.model,
        thread_context=thread_context,
    )

    reconciler_deps.user_id = user_context.user_id
    reconciler_deps.org_id = user_context.org_id

    # Recreate request with body for handle_ag_ui_request
    async def receive():
        return {"type": "http.request", "body": body_bytes}

    new_request = Request(
        scope=request.scope,
        receive=receive,
    )
    summary_func = create_save_summary_async(
        thread_id=thread_id,
        run_id=run_id,
        deps=reconciler_deps,
    )
    return await handle_ag_ui_request_with_thinking(
        agent=reconciler_orchestrator,
        request=new_request,
        deps=reconciler_deps,
        on_complete=summary_func,
    )


# ============================================================================
# Tickets API Endpoints
# ============================================================================


@app.get("/tickets")
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    created_by: str | None = None,
    limit: int = 50,
    state: AppState = Depends(get_app_state),  # noqa: B008 expected for fastapi
):
    """List tickets with optional filtering.

    Query params:
        status: Filter by status (open, in_progress, blocked, completed, cancelled)
        priority: Filter by priority (low, medium, high, urgent)
        assigned_to: Filter by assignee
        created_by: Filter by creator
        limit: Max results (default 50)
    """
    if not state.ticket_storage:
        return {"tickets": [], "count": 0, "error": "Ticket storage not configured"}

    try:
        from lineage.backends.tickets.protocol import TicketPriority, TicketStatus

        status_enum = TicketStatus(status) if status else None
        priority_enum = TicketPriority(priority) if priority else None

        tickets = await state.ticket_storage.list_tickets(
            status=status_enum,
            priority=priority_enum,
            assigned_to=assigned_to,
            created_by=created_by,
            limit=limit,
        )

        ticket_dicts = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description or "",
                "status": t.status.value if t.status else "",
                "priority": t.priority.value if t.priority else "",
                "created_by": t.created_by,
                "assigned_to": t.assigned_to,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                "tags": t.tags or [],
            }
            for t in tickets
        ]

        return {"tickets": ticket_dicts, "count": len(ticket_dicts)}

    except Exception as e:
        logger.error(f"Failed to list tickets: {e}")
        return {"tickets": [], "count": 0, "error": str(e)}


@app.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    state: AppState = Depends(get_app_state),  # noqa: B008 expected for fastapi
):
    """Get a specific ticket by ID."""
    if not state.ticket_storage:
        return {"error": "Ticket storage not configured"}

    try:
        ticket = await state.ticket_storage.get_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket not found: {ticket_id}"}

        return {"ticket": ticket.to_dict()}

    except Exception as e:
        logger.error(f"Failed to get ticket {ticket_id}: {e}")
        return {"error": str(e)}


# ============================================================================
# Reports Endpoints
# ============================================================================


@app.get("/reports")
async def list_reports(state: AppState = Depends(get_app_state)): #noqa: B008 expected for fastapi
    """List all saved reports using the reports backend."""
    if not state.reports_backend:
        return {"reports": [], "error": "Reports backend not initialized"}

    try:
        report_metadata_list = state.reports_backend.list_reports()
        reports = []
        for metadata in report_metadata_list:
            reports.append(
                {
                    "report_id": metadata.report_id,
                    "title": metadata.title,
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat(),
                    "cell_count": metadata.cell_count,
                    "url": f"/reports/{metadata.report_id}",
                    "export_url": f"/reports/{metadata.report_id}/export",
                }
            )
        return {"reports": reports, "count": len(reports)}
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        return {"reports": [], "error": str(e)}


@app.get("/reports/{report_id}")
async def get_report(report_id: str, state: AppState = Depends(get_app_state)): #noqa: B008 expected for fastapi
    """Get a specific report's data (JSON format)."""
    if not state.reports_backend:
        return {"error": "Reports backend not initialized"}

    try:
        report = state.reports_backend.get_report(report_id)
        return {
            "report_id": report.report_id,
            "title": report.title,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
            "cells": [cell.model_dump() for cell in report.cells],
        }
    except FileNotFoundError:
        return HTMLResponse(
            content=f"<h1>Report not found: {report_id}</h1>", status_code=404
        )
    except Exception as e:
        logger.error(f"Error fetching report {report_id}: {e}")
        return {"error": str(e)}


@app.post("/reports/{report_id}/export")
async def generate_and_export_report(
    report_id: str, state: AppState = Depends(get_app_state), #noqa: B008 expected for fastapi
):
    """Generate HTML export on-demand and return for download.

    This endpoint generates a standalone HTML file from the report data
    and returns it for immediate download. No agent interaction required.
    """
    if not state.reports_backend:
        return HTMLResponse(
            content="<h1>Reports backend not initialized</h1>", status_code=500
        )

    try:
        # Get report from backend
        report = state.reports_backend.get_report(report_id)

        # Generate standalone HTML
        html_content = generate_standalone_html(report)

        # Save to report directory (for caching/future GET requests)
        report_dir = state.reports_backend.get_report_dir(report_id)
        html_path = report_dir / "report.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Return file for download
        filename = f"{report.title.replace(' ', '_').replace('/', '_')}.html"
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except FileNotFoundError:
        return HTMLResponse(
            content=f"<h1>Report not found: {report_id}</h1>", status_code=404
        )
    except Exception as e:
        logger.error(f"Error exporting report {report_id}: {e}")
        return HTMLResponse(
            content=f"<h1>Error exporting report: {str(e)}</h1>", status_code=500
        )


@app.get("/reports/{report_id}/export")
async def export_report(report_id: str, state: AppState = Depends(get_app_state)): #noqa: B008 expected for fastapi
    """Export a report as standalone HTML file (serves pre-generated HTML)."""
    if not state.reports_backend:
        return HTMLResponse(
            content="<h1>Reports backend not initialized</h1>", status_code=500
        )

    try:
        report_dir = state.reports_backend.get_report_dir(report_id)
        html_path = report_dir / "report.html"

        if not html_path.exists():
            return HTMLResponse(
                content=f"<h1>Report HTML not found for: {report_id}</h1><p>Generate it via /reports/{report_id}/export first.</p>",
                status_code=404,
            )

        return FileResponse(html_path, media_type="text/html")
    except FileNotFoundError:
        return HTMLResponse(
            content=f"<h1>Report not found: {report_id}</h1>", status_code=404
        )
    except Exception as e:
        logger.error(f"Error exporting report {report_id}: {e}")
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>", status_code=500)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the backend server."""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting server on http://localhost:{port}")

    uvicorn.run(
        app,
        host="0.0.0.0",  # nosec B104: intentional binding
        port=port,
        log_level="info",
        access_log=True,  # Enable access logs
        log_config=None,  # Use our logging config instead of uvicorn's default
    )


if __name__ == "__main__":
    main()

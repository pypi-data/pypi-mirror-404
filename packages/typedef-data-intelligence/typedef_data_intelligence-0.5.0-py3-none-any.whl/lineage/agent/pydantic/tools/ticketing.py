"""Ticket management tools for PydanticAI agents.

This module provides tool functions that agents can use to interact with
the ticket management system for inter-agent communication and work tracking.

Available Tools:
- create_ticket: Create a new ticket for work or communication
- list_tickets: List tickets with optional filtering
- get_ticket: Get full details of a specific ticket
- update_ticket: Update ticket status, priority, assignee, or tags
- add_ticket_comment: Add a comment to a ticket

All tools gracefully handle cases where ticket backend is unavailable.
"""

from __future__ import annotations

import logging
from typing import List, Literal, Optional

from pydantic_ai import RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.types import (
    AgentDeps,
    CreateTicketResult,
    ListTicketsResult,
    GetTicketResult,
    UpdateTicketResult,
    AddTicketCommentResult,
)
from lineage.backends.tickets.protocol import TicketPriority, TicketStatus
from pydantic_ai.toolsets import FunctionToolset

logger = logging.getLogger(__name__)


# ============================================================================
# Ticket Management Tools
# ============================================================================
ticketing_toolset = FunctionToolset()

@ticketing_toolset.tool
@safe_tool
async def create_ticket(
    ctx: RunContext[AgentDeps],
    title: str,
    description: str,
    priority: Literal["low", "medium", "high", "urgent"],
    assigned_to: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> CreateTicketResult | ToolError:
    """Create a new ticket for work that needs to be done or to communicate with other agents.

    Tickets are auditable and persistent across agent sessions.

    Args:
        title: Short title/summary of the ticket
        description: Detailed description of the work or communication
        priority: Priority level (low, medium, high, urgent)
        assigned_to: Optional agent name to assign this ticket to
        tags: Optional tags for categorization (e.g., ['dbt', 'modeling'], ['data-quality'])

    Returns:
        Created ticket details or error

    Example:
        ```python
        result = create_ticket(
            ctx,
            title="Fix data quality issue in fct_revenue",
            description="Discovered null customer_id values in fct_revenue affecting ARR calculations",
            priority="high",
            assigned_to="data-explorer",
            tags=["data-quality", "fct_revenue"]
        )
        ```

    Note:
        - Use descriptive titles that summarize the work
        - Include enough context in description for others to understand
        - Set appropriate priority based on urgency and impact
        - Use tags consistently for easier filtering
    """
    # Check if ticket backend is available
    if not ctx.deps.ticket_storage:
        logger.debug("Ticket storage not available")
        return tool_error("Ticket storage not configured (graceful degradation)")

    try:
        # Convert priority string to enum
        priority_enum = TicketPriority(priority)

        logger.info(f"Creating ticket: title={title}, description={description}, priority={priority}, assigned_to={assigned_to}, tags={tags}, ticket_storage={ctx.deps.ticket_storage} agent_name={ctx.deps.agent_name}   ")
        # Create ticket
        ticket = await ctx.deps.ticket_storage.create_ticket(
            title=title,
            description=description,
            priority=priority_enum,
            created_by=ctx.deps.agent_name,
            assigned_to=assigned_to,
            tags=tags,
        )

        logger.info(
            f"Created ticket: id={ticket.id}, title={ticket.title}, "
            f"priority={priority}, assigned_to={assigned_to}"
        )

        # Store typed result in state for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        result = CreateTicketResult(
            ticket_id=ticket.id,
            title=ticket.title,
            status=ticket.status.value if ticket.status else "",
            priority=ticket.priority.value if ticket.priority else "",
            message=f"Created ticket {ticket.id}: {ticket.title}",
        )
        ctx.deps.state.tool_results[tool_call_id] = result

        return result

    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        return tool_error(f"Failed to create ticket: {str(e)}")

@ticketing_toolset.tool
@safe_tool
async def list_tickets(
    ctx: RunContext[AgentDeps],
    status: Optional[Literal["open", "in_progress", "blocked", "completed", "cancelled"]] = None,
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = None,
    assigned_to: Optional[str] = None,
    created_by: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
) -> ListTicketsResult | ToolError:
    """List tickets with optional filtering.

    Returns tickets sorted by most recently updated first.

    Args:
        status: Filter by ticket status (open, in_progress, blocked, completed, cancelled)
        priority: Filter by priority (low, medium, high, urgent)
        assigned_to: Filter by assignee (agent name)
        created_by: Filter by creator (agent name)
        tags: Filter by tags (must have all specified tags)
        limit: Maximum number of tickets to return (default: 50)

    Returns:
        List of matching tickets or error

    Example:
        ```python
        # List all open high-priority tickets
        result = list_tickets(ctx, status="open", priority="high")

        # List tickets assigned to specific agent
        result = list_tickets(ctx, assigned_to="data-explorer")

        # List tickets with specific tags
        result = list_tickets(ctx, tags=["data-quality", "urgent"])
        ```

    Note:
        - Returns tickets sorted by updated_at DESC (most recent first)
        - All filters are optional - omit for no filtering
        - Tags filter requires ALL specified tags to match
    """
    # Check if ticket backend is available
    if not ctx.deps.ticket_storage:
        logger.debug("Ticket storage not available")
        return tool_error("Ticket storage not configured (graceful degradation)")

    try:
        # Convert string filters to enums if provided
        status_enum = TicketStatus(status) if status else None
        priority_enum = TicketPriority(priority) if priority else None

        # List tickets with filters
        tickets = await ctx.deps.ticket_storage.list_tickets(
            status=status_enum,
            priority=priority_enum,
            assigned_to=assigned_to,
            created_by=created_by,
            tags=tags,
            limit=limit,
        )

        # Convert to dicts for response
        ticket_dicts = [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value if t.status else "",
                "priority": t.priority.value if t.priority else "",
                "created_by": t.created_by,
                "assigned_to": t.assigned_to,
                "updated_at": t.updated_at.isoformat(),
                "tags": t.tags,
            }
            for t in tickets
        ]

        logger.info(
            f"Listed tickets: status={status}, priority={priority}, "
            f"assigned_to={assigned_to}, count={len(tickets)}"
        )

        # Store typed result in state for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        result = ListTicketsResult(
            tickets=ticket_dicts,
            count=len(ticket_dicts),
        )
        ctx.deps.state.tool_results[tool_call_id] = result

        return result

    except Exception as e:
        logger.error(f"Failed to list tickets: {e}")
        return tool_error(f"Failed to list tickets: {str(e)}")


@ticketing_toolset.tool
@safe_tool
async def get_ticket(
    ctx: RunContext[AgentDeps],
    ticket_id: str,
) -> GetTicketResult | ToolError:
    """Get full details of a specific ticket by ID.

    Args:
        ticket_id: Ticket ID

    Returns:
        Full ticket details including comments or error

    Example:
        ```python
        result = get_ticket(ctx, ticket_id="abc123")
        # Returns complete ticket data including all comments
        ```

    Note:
        - Returns full ticket details including all comments
        - Use list_tickets() to discover ticket IDs
    """
    # Check if ticket backend is available
    if not ctx.deps.ticket_storage:
        logger.debug("Ticket storage not available")
        return tool_error("Ticket storage not configured (graceful degradation)")

    try:
        # Get ticket
        ticket = await ctx.deps.ticket_storage.get_ticket(ticket_id)

        if ticket is None:
            return tool_error(f"Ticket not found: {ticket_id}")

        logger.info(f"Retrieved ticket: id={ticket.id}, title={ticket.title}")

        # Store typed result in state for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        result = GetTicketResult(
            ticket=ticket.to_dict(),
        )
        ctx.deps.state.tool_results[tool_call_id] = result

        return result

    except Exception as e:
        logger.error(f"Failed to get ticket: {e}")
        return tool_error(f"Failed to get ticket: {str(e)}")


@ticketing_toolset.tool
@safe_tool
async def update_ticket(
    ctx: RunContext[AgentDeps],
    ticket_id: str,
    status: Optional[Literal["open", "in_progress", "blocked", "completed", "cancelled"]] = None,
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = None,
    assigned_to: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> UpdateTicketResult | ToolError:
    """Update ticket status, priority, assignee, or tags.

    Use this to mark tickets as in_progress, blocked, or completed.

    Args:
        ticket_id: Ticket ID
        status: New status (open, in_progress, blocked, completed, cancelled)
        priority: New priority (low, medium, high, urgent)
        assigned_to: New assignee (agent name)
        tags: New tags (replaces existing tags)

    Returns:
        Updated ticket confirmation or error

    Example:
        ```python
        # Mark ticket as in progress
        result = update_ticket(ctx, ticket_id="abc123", status="in_progress")

        # Reassign ticket and increase priority
        result = update_ticket(
            ctx,
            ticket_id="abc123",
            assigned_to="troubleshooter",
            priority="urgent"
        )

        # Mark ticket as completed
        result = update_ticket(ctx, ticket_id="abc123", status="completed")
        ```

    Note:
        - At least one field must be provided
        - Tags completely replace existing tags (not append)
        - Status "completed" automatically sets completed_at timestamp
    """
    # Check if ticket backend is available
    if not ctx.deps.ticket_storage:
        logger.debug("Ticket storage not available")
        return tool_error("Ticket storage not configured (graceful degradation)")

    try:
        # Convert string filters to enums if provided
        # Otherwise, use the default values
        status_enum = TicketStatus(status) if status else TicketStatus.OPEN
        priority_enum = TicketPriority(priority) if priority else TicketPriority.MEDIUM

        # Update ticket
        ticket = await ctx.deps.ticket_storage.update_ticket(
            ticket_id=ticket_id,
            status=status_enum,
            priority=priority_enum,
            assigned_to=assigned_to,
            tags=tags,
        )

        logger.info(
            f"Updated ticket: id={ticket.id}, status={status}, "
            f"priority={priority}, assigned_to={assigned_to}"
        )

        # Store typed result in state for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        result = UpdateTicketResult(
            ticket_id=ticket.id,
            message=f"Updated ticket {ticket.id}",
        )
        ctx.deps.state.tool_results[tool_call_id] = result

        return result

    except ValueError as e:
        logger.error(f"Failed to update ticket: {e}")
        return tool_error(str(e))
    except Exception as e:
        logger.error(f"Failed to update ticket: {e}")
        return tool_error(f"Failed to update ticket: {str(e)}")


@ticketing_toolset.tool
@safe_tool
async def add_ticket_comment(
    ctx: RunContext[AgentDeps],
    ticket_id: str,
    comment: str,
) -> AddTicketCommentResult | ToolError:
    """Add a comment to a ticket.

    Use this to provide updates, ask questions, or document progress.

    Args:
        ticket_id: Ticket ID
        comment: Comment text

    Returns:
        Comment confirmation or error

    Example:
        ```python
        result = add_ticket_comment(
            ctx,
            ticket_id="abc123",
            comment="Started investigation. Found that the issue is caused by missing "
                    "foreign key constraint between fct_revenue and dim_customers."
        )
        ```

    Note:
        - Comments are timestamped and attributed to the current agent
        - Comments are visible in full ticket details (get_ticket)
        - Use for significant updates or blockers
    """
    # Check if ticket backend is available
    if not ctx.deps.ticket_storage:
        logger.debug("Ticket storage not available")
        return tool_error("Ticket storage not configured (graceful degradation)")

    try:
        # Add comment
        ticket = await ctx.deps.ticket_storage.add_comment(
            ticket_id=ticket_id,
            author=ctx.deps.agent_name,
            comment=comment,
        )

        logger.info(
            f"Added comment to ticket: id={ticket.id}, author={ctx.deps.agent_name}"
        )

        # Store typed result in state for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        result = AddTicketCommentResult(
            ticket_id=ticket.id,
            message=f"Added comment to ticket {ticket.id}",
        )
        ctx.deps.state.tool_results[tool_call_id] = result

        return result

    except ValueError as e:
        logger.error(f"Failed to add comment: {e}")
        return tool_error(str(e))
    except Exception as e:
        logger.error(f"Failed to add comment: {e}")
        return tool_error(f"Failed to add comment: {str(e)}")


__all__ = [
    "create_ticket",
    "list_tickets",
    "get_ticket",
    "update_ticket",
    "add_ticket_comment",
    "ticketing_toolset",
]

"""Daemon mode screen for autonomous ticket processing.

This module provides a TUI screen for running agents in daemon mode,
automatically processing tickets from Linear or other ticket backends.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    DataTable,
    Label,
    Log,
    Static,
)

from lineage.ag_ui.client import AGUIClient

logger = logging.getLogger(__name__)

# ============================================================================
# Constants from de_daemon.py
# ============================================================================

DE_AGENT_LABEL = "ingest-critical"
DATA_ENGINEER_ASSIGNEE = "data-engineer-agent"
# Single source of truth for processable statuses and their precedence (in_progress checked before open)
PROCESSABLE_TICKET_STATUSES = ["in_progress", "open"]
POLL_WAIT_MIN = 2
POLL_WAIT_MAX = 600

# Prompts for different ticket states
PROMPT_ASSIGNED_OPEN = (
    "Please work on the ticket {ticket_id}, providing a summary as a comment to the ticket. "
    "If you need clarification, reassign the ticket to the creator. "
    "If you completed the ticket, mark it 'in_review' and reassign it to the creator."
)

PROMPT_ASSIGNED_IN_PROGRESS = (
    "Please continue working on the ticket {ticket_id}, providing a summary as a comment to the ticket. "
    "If you need clarification, reassign the ticket to the creator. "
    "If you completed the ticket, mark it 'in_review' and reassign it to the creator."
)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class TicketInfo:
    """Ticket information for display."""
    id: str
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    tags: List[str] = None
    labels: List[str] = None  # Some systems use labels instead of tags

    def __post_init__(self):
        """Post-initialize the ticket info."""
        if self.tags is None:
            self.tags = []
        if self.labels is None:
            self.labels = []


# ============================================================================
# Widgets
# ============================================================================


class DaemonControls(Horizontal):
    """Control buttons for daemon operation with agent type selector."""

    def compose(self) -> ComposeResult:
        """Compose the daemon controls."""
        yield Button("▶ Start", id="start-daemon", variant="success")
        yield Button("⏹ Stop", id="stop-daemon", variant="error", disabled=True)
        yield Static(" │ ", classes="separator")
        yield Button("Reconciler", id="btn-reconciler", variant="primary")
        yield Button("Investigator", id="btn-investigator", variant="default")


class TicketQueueTable(DataTable):
    """Table showing pending tickets in priority order."""

    def on_mount(self) -> None:
        """Set up table columns."""
        self.add_columns("Priority", "ID", "Title", "Tags", "Status", "Assigned", "Process?")
        self.cursor_type = "row"

    def update_tickets(self, tickets: List[TicketInfo]) -> None:
        """Update table with new ticket list."""
        self.clear()
        for ticket in tickets:
            priority_icon = self._priority_icon(ticket.priority)
            # Increase title to 60 chars (was 40)
            title_display = ticket.title[:60] + ("..." if len(ticket.title) > 60 else "")
            # Format tags as comma-separated, show first 3
            tags_display = ", ".join(ticket.tags[:3]) if ticket.tags else ""
            if ticket.tags and len(ticket.tags) > 3:
                tags_display += f" +{len(ticket.tags) - 3}"
            # Indicate whether this ticket will actually be picked up by the daemon loop.
            # This must match the filtering logic in `_get_next_ticket`.
            will_process = (
                "✓"
                if ticket.assigned_to == DATA_ENGINEER_ASSIGNEE
                and ticket.status.lower() in PROCESSABLE_TICKET_STATUSES
                else "-"
            )
            self.add_row(
                priority_icon,
                ticket.id[:12],  # Truncate long IDs
                title_display,
                tags_display or "-",
                ticket.status,
                ticket.assigned_to or "-",
                will_process,
                key=ticket.id,
            )

    def _priority_icon(self, priority: str) -> str:
        """Get icon for priority level."""
        icons = {
            "urgent": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }
        return icons.get(priority, "⚪")


class DaemonLog(Log):
    """Real-time log of daemon activity."""

    def log_info(self, message: str) -> None:
        """Log an info message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write_line(f"[{timestamp}] {message}")

    def log_error(self, message: str) -> None:
        """Log an error message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write_line(f"[{timestamp}] ❌ {message}")

    def log_success(self, message: str) -> None:
        """Log a success message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write_line(f"[{timestamp}] ✅ {message}")

    def log_processing(self, ticket_id: str) -> None:
        """Log that we're processing a ticket."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write_line(f"[{timestamp}] 🔄 Processing ticket: {ticket_id}")

    def log_tool_call(self, tool_name: str, args: Optional[Dict] = None) -> None:
        """Log a tool call with optional arguments."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        display = _format_daemon_tool_display(tool_name, args or {})
        self.write_line(f"[{timestamp}] {display}")


# Tool display info for daemon log
DAEMON_TOOL_DISPLAY = {
    # Tickets
    "create_ticket": {"verb": "Creating ticket", "icon": "🎫"},
    "list_tickets": {"verb": "Fetching tickets", "icon": "📋"},
    "get_ticket": {"verb": "Loading ticket", "icon": "🔖"},
    "update_ticket": {"verb": "Updating ticket", "icon": "🔄"},
    "add_ticket_comment": {"verb": "Adding comment", "icon": "💬"},
    # Knowledge Graph
    "query_graph": {"verb": "Querying graph", "icon": "🔍"},
    "get_model_semantics": {"verb": "Analyzing model", "icon": "🧠"},
    "get_downstream_impact": {"verb": "Checking impact", "icon": "📉"},
    # Warehouse
    "execute_query": {"verb": "Running SQL", "icon": "🔎"},
    "preview_table": {"verb": "Sampling data", "icon": "👀"},
    # Reports
    "create_report": {"verb": "Creating report", "icon": "📄"},
    # Memory
    "store_memory": {"verb": "Saving to memory", "icon": "💾"},
    "search_memory": {"verb": "Searching memory", "icon": "🔍"},
}


def _format_daemon_tool_display(tool_name: str, args: Dict) -> str:
    """Format tool call for daemon activity log."""
    info = DAEMON_TOOL_DISPLAY.get(tool_name, {"verb": tool_name, "icon": "🔧"})

    # Ticket-specific formatting
    if tool_name == "create_ticket":
        title = args.get("title", "")
        if title:
            return f"{info['icon']} {info['verb']}: \"{title[:40]}{'...' if len(title) > 40 else ''}\""

    if tool_name == "get_ticket":
        ticket_id = args.get("ticket_id", "")
        if ticket_id:
            return f"{info['icon']} {info['verb']}: {ticket_id}"

    if tool_name == "list_tickets":
        filters = []
        if args.get("status"):
            filters.append(f"status={args['status']}")
        if args.get("assigned_to"):
            filters.append(f"assigned={args['assigned_to']}")
        if filters:
            return f"{info['icon']} {info['verb']} ({', '.join(filters)})"

    if tool_name == "update_ticket":
        ticket_id = args.get("ticket_id", "")
        updates = []
        if args.get("status"):
            updates.append(f"status→{args['status']}")
        if args.get("assigned_to"):
            updates.append(f"→{args['assigned_to']}")
        if ticket_id:
            update_str = f": {', '.join(updates)}" if updates else ""
            return f"{info['icon']} {info['verb']} {ticket_id}{update_str}"

    if tool_name == "add_ticket_comment":
        ticket_id = args.get("ticket_id", "")
        if ticket_id:
            return f"{info['icon']} {info['verb']} to {ticket_id}"

    # Default
    return f"{info['icon']} {info['verb']}..."


# ============================================================================
# Main Daemon Screen
# ============================================================================


class DaemonScreen(Container):
    """Main daemon screen with controls, ticket queue, and activity log."""

    DEFAULT_CSS = """
    DaemonScreen {
        layout: vertical;
        height: 100%;
        padding: 1;
    }

    DaemonControls {
        height: 3;
        margin: 1 0;
    }

    DaemonControls Button {
        margin: 0 1;
    }

    DaemonControls .separator {
        width: auto;
        padding: 0;
    }

    TicketQueueTable {
        height: 10;
        border: solid $primary;
    }

    DaemonLog {
        height: 1fr;
        border: solid $primary;
        margin-top: 1;
    }
    """

    def __init__(self, client: AGUIClient, agent_type: str = "reconciler"):
        """Initialize the daemon screen.

        Args:
            client: AGUIClient for communicating with backend
            agent_type: Initial agent type ("reconciler" or "investigator")
        """
        super().__init__()
        self.client = client
        self.agent_type = agent_type
        self._daemon_task: Optional[asyncio.Task] = None
        self._poll_wait = POLL_WAIT_MIN
        self._tickets: List[TicketInfo] = []

    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        yield DaemonControls(id="daemon-controls")
        yield Label("Pending Tickets:", classes="section-label")
        yield TicketQueueTable(id="ticket-queue")
        yield Label("Activity Log:", classes="section-label")
        yield DaemonLog(id="daemon-log")

    def on_mount(self) -> None:
        """Initialize on mount."""
        self.log.log_info("Daemon screen initialized. Press Start to begin.")

    @property
    def log(self) -> DaemonLog:
        """Get the log widget."""
        return self.query_one("#daemon-log", DaemonLog)

    @property
    def ticket_queue(self) -> TicketQueueTable:
        """Get the ticket queue table."""
        return self.query_one("#ticket-queue", TicketQueueTable)

    @property
    def controls(self) -> DaemonControls:
        """Get the controls container."""
        return self.query_one("#daemon-controls", DaemonControls)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle control button presses."""
        button_id = event.button.id
        if button_id == "start-daemon":
            asyncio.create_task(self.start_daemon())
        elif button_id == "stop-daemon":
            asyncio.create_task(self.stop_daemon())
        elif button_id == "btn-reconciler":
            self._set_agent_type("reconciler")
        elif button_id == "btn-investigator":
            self._set_agent_type("investigator")

    def _set_agent_type(self, agent_type: str) -> None:
        """Switch agent type and update button states."""
        self.agent_type = agent_type
        self.log.log_info(f"Switched to {agent_type.title()} agent")
        # Update button variants to show which is selected
        self.query_one("#btn-reconciler", Button).variant = "primary" if agent_type == "reconciler" else "default"
        self.query_one("#btn-investigator", Button).variant = "primary" if agent_type == "investigator" else "default"

    async def start_daemon(self) -> None:
        """Start the daemon polling loop."""
        if self._daemon_task and not self._daemon_task.done():
            self.log.log_info("Daemon already running")
            return

        self._poll_wait = POLL_WAIT_MIN

        # Update button states
        self.query_one("#start-daemon", Button).disabled = True
        self.query_one("#stop-daemon", Button).disabled = False

        statuses = ", ".join(PROCESSABLE_TICKET_STATUSES)
        self.log.log_info(
            f"Starting daemon with {self.agent_type} agent (processing {statuses} tickets assigned to {DATA_ENGINEER_ASSIGNEE})..."
        )
        self._daemon_task = asyncio.create_task(self._run_daemon_loop())

    async def stop_daemon(self) -> None:
        """Stop the daemon completely."""
        if self._daemon_task:
            self._daemon_task.cancel()
            try:
                await self._daemon_task
            except asyncio.CancelledError:
                pass
            self._daemon_task = None

        self.log.log_info("Daemon stopped.")

        # Update button states
        self.query_one("#start-daemon", Button).disabled = False
        self.query_one("#stop-daemon", Button).disabled = True

    async def _run_daemon_loop(self) -> None:
        """Main daemon loop that polls for and processes tickets."""
        while True:
            try:
                # Only process tickets assigned to the data engineer user
                assignee = DATA_ENGINEER_ASSIGNEE

                # Refresh ticket queue
                await self._refresh_ticket_queue()

                # Find ticket to process
                ticket = await self._get_next_ticket(assignee)

                if ticket:
                    await self._process_ticket(ticket)
                    self._poll_wait = POLL_WAIT_MIN
                    # Wait a bit before checking for the next ticket to avoid race conditions
                    # and allow backend state to settle
                    await asyncio.sleep(self._poll_wait)
                else:
                    # No tickets - exponential backoff
                    self._poll_wait = min(POLL_WAIT_MAX, self._poll_wait * 2)
                    self.log.log_info(f"No tickets found. Waiting {self._poll_wait}s...")
                    await asyncio.sleep(self._poll_wait)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log.log_error(f"Error in daemon loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _refresh_ticket_queue(self) -> None:
        """Refresh the ticket queue from the backend."""
        try:
            # Call the tickets API endpoint using httpx client
            response = await self.client.http_client.get(
                f"{self.client.base_url}/tickets",
                params={"limit": 50},
            )
            if response.status_code == 200:
                data = response.json()
                tickets = data.get("tickets", [])

                # Convert to TicketInfo objects
                self._tickets = [
                    TicketInfo(
                        id=t["id"],
                        title=t["title"],
                        status=t["status"],
                        priority=t["priority"],
                        assigned_to=t.get("assigned_to"),
                        tags=t.get("tags", []),
                    )
                    for t in tickets
                ]

                # Update the table display
                self.ticket_queue.update_tickets(self._tickets)

        except Exception as e:
            logger.debug(f"Failed to refresh ticket queue: {e}")

    async def _get_next_ticket(self, assignee: str) -> Optional[TicketInfo]:
        """Get the next ticket to process.

        Priority order:
        1. In-progress tickets assigned to this agent
        2. Open tickets assigned to this agent

        Args:
            assignee: The agent name to filter by

        Returns:
            Next ticket to process, or None if no tickets found
        """
        try:
            # Check for the next ticket by status precedence.
            for status in PROCESSABLE_TICKET_STATUSES:
                # Normalize status to lowercase for consistent API queries
                # (matches the case-insensitive check in display logic)
                response = await self.client.http_client.get(
                    f"{self.client.base_url}/tickets",
                    params={"status": status.lower(), "assigned_to": assignee, "limit": 1},
                )
                if response.status_code == 200:
                    data = response.json()
                    tickets = data.get("tickets", [])
                    if tickets:
                        t = tickets[0]
                        return TicketInfo(
                            id=t["id"],
                            title=t["title"],
                            status=t["status"],
                            priority=t["priority"],
                            assigned_to=t.get("assigned_to"),
                            tags=t.get("tags", []),
                        )

            return None

        except Exception as e:
            logger.debug(f"Failed to get next ticket: {e}")
            return None

    async def _process_ticket(self, ticket: TicketInfo) -> None:
        """Process a single ticket by running the agent.

        Args:
            ticket: Ticket to process
        """
        self.log.log_processing(ticket.id)

        # Determine prompt based on ticket status
        if ticket.status == "in_progress":
            prompt = PROMPT_ASSIGNED_IN_PROGRESS.format(ticket_id=ticket.id)
        else:
            prompt = PROMPT_ASSIGNED_OPEN.format(ticket_id=ticket.id)

        # Generate unique IDs for this run
        thread_id = f"daemon-{self.agent_type}-{ticket.id}"
        run_id = str(uuid.uuid4())

        try:
            # Stream agent response
            response_text = ""
            async for event in self.client.stream_agent(
                agent_name=self.agent_type,
                message=prompt,
                thread_id=thread_id,
                run_id=run_id,
            ):
                event_type = event.get("type", "")

                # Log key events
                if event_type == "TEXT_MESSAGE_CONTENT":
                    delta = event.get("delta", "")
                    response_text += delta

                elif event_type == "TOOL_CALL_START":
                    # Try multiple paths for tool name (AG-UI format varies)
                    tool_name = (
                        event.get("toolCallName")
                        or event.get("tool", {}).get("name")
                        or event.get("name")
                        or event.get("tool_name")
                        or "unknown"
                    )
                    # Extract tool arguments for better display
                    tool_args = event.get("toolCallArgs", {})
                    if isinstance(tool_args, str):
                        try:
                            import json
                            tool_args = json.loads(tool_args)
                        except (json.JSONDecodeError, TypeError):
                            tool_args = {}
                    self.log.log_tool_call(tool_name, tool_args)

                elif event_type == "RUN_FINISHED":
                    self.log.log_success(f"Completed ticket {ticket.id}")

                elif event_type == "RUN_ERROR":
                    error = event.get("error", "Unknown error")
                    self.log.log_error(f"Agent error: {error}")

        except Exception as e:
            self.log.log_error(f"Failed to process ticket {ticket.id}: {e}")

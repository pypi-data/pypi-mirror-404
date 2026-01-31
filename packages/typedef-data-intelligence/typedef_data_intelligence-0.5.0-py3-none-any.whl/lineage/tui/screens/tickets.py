"""Interactive ticket browsing and work screen.

This module provides a TUI screen for browsing tickets interactively,
viewing ticket details, and opening tickets in agent chat tabs.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.message import Message as TextualMessage
from textual.widgets import Button, DataTable, Label, Static

from lineage.ag_ui.client import AGUIClient

logger = logging.getLogger(__name__)


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
    description: str = ""
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)


class OpenTicketInChat(TextualMessage):
    """Message to open a ticket in the chat interface."""

    def __init__(self, ticket: TicketInfo, agent_type: str) -> None:
        """Initialize the message.

        Args:
            ticket: The ticket to open in chat
            agent_type: The agent type to use (copilot or investigator)
        """
        super().__init__()
        self.ticket = ticket
        self.agent_type = agent_type


# ============================================================================
# Widgets
# ============================================================================


class TicketsControls(Horizontal):
    """Control buttons for ticket browsing."""

    def compose(self) -> ComposeResult:
        """Create the control buttons layout."""
        yield Button("Refresh", id="refresh-tickets", variant="primary")
        yield Static(" | ", classes="separator")
        yield Button("Investigator", id="work-investigator", variant="warning", disabled=True)
        yield Button("Copilot", id="work-copilot", variant="success", disabled=True)


class TicketDetailsPanel(VerticalScroll):
    """Scrollable panel showing selected ticket details."""

    DEFAULT_CSS = """
    TicketDetailsPanel {
        height: 15;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    TicketDetailsPanel Label {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the details panel layout."""
        yield Label("Select a ticket to view details", id="ticket-details-content")

    def show_ticket(self, ticket: TicketInfo) -> None:
        """Display full ticket details including description."""
        content = self.query_one("#ticket-details-content", Label)
        details = (
            f"{ticket.title}\n"
            f"{'─' * 60}\n"
            f"ID: {ticket.id} | Status: {ticket.status} | Priority: {ticket.priority}\n"
            f"Assigned: {ticket.assigned_to or 'Unassigned'}\n"
            f"Tags: {', '.join(ticket.tags) if ticket.tags else 'None'}"
        )
        if ticket.description:
            # Show full description
            details += f"\n\n{ticket.description}"
        content.update(details)

    def clear(self) -> None:
        """Clear the details panel."""
        content = self.query_one("#ticket-details-content", Label)
        content.update("Select a ticket to view details")


class TicketsTable(DataTable):
    """Table showing tickets."""

    def on_mount(self) -> None:
        """Set up table columns."""
        self.add_columns("Priority", "ID", "Title", "Tags", "Status", "Assigned")
        self.cursor_type = "row"

    def update_tickets(self, tickets: List[TicketInfo]) -> None:
        """Update table with new ticket list."""
        self.clear()
        for ticket in tickets:
            priority_icon = self._priority_icon(ticket.priority)
            # Truncate long titles
            title_display = ticket.title[:60] + ("..." if len(ticket.title) > 60 else "")
            # Format tags
            tags_display = ", ".join(ticket.tags[:3]) if ticket.tags else ""
            if ticket.tags and len(ticket.tags) > 3:
                tags_display += f" +{len(ticket.tags) - 3}"
            self.add_row(
                priority_icon,
                ticket.id[:12],
                title_display,
                tags_display or "-",
                ticket.status,
                ticket.assigned_to or "-",
                key=ticket.id,
            )

    def _priority_icon(self, priority: str) -> str:
        """Get icon for priority level."""
        icons = {"urgent": "!", "high": "H", "medium": "M", "low": "L"}
        return icons.get(priority.lower(), "?")


# ============================================================================
# Main Tickets Screen
# ============================================================================


class TicketsScreen(Container):
    """Interactive ticket browsing screen."""

    DEFAULT_CSS = """
    TicketsScreen {
        layout: vertical;
        height: 100%;
        padding: 1;
    }

    TicketsControls {
        height: 3;
        margin: 1 0;
    }

    TicketsControls Button {
        margin: 0 1;
    }

    TicketsControls .separator {
        width: auto;
        padding: 0;
    }

    TicketsTable {
        height: 1fr;
        border: solid $primary;
    }
    """

    def __init__(self, client: AGUIClient):
        """Initialize the tickets screen.

        Args:
            client: AGUIClient for communicating with backend
        """
        super().__init__()
        self.client = client
        self._tickets: List[TicketInfo] = []
        self.selected_ticket: Optional[TicketInfo] = None

    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        yield Label("Tickets", classes="section-label")
        yield TicketsControls(id="tickets-controls")
        yield TicketDetailsPanel(id="ticket-details")
        yield TicketsTable(id="tickets-table")

    async def on_mount(self) -> None:
        """Initialize on mount - do NOT auto-refresh to avoid startup delay.

        Tickets are only fetched when the user clicks the Refresh button.
        """
        pass

    @property
    def details_panel(self) -> TicketDetailsPanel:
        """Get the details panel widget."""
        return self.query_one("#ticket-details", TicketDetailsPanel)

    @property
    def tickets_table(self) -> TicketsTable:
        """Get the tickets table widget."""
        return self.query_one("#tickets-table", TicketsTable)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle control button presses."""
        button_id = event.button.id
        if button_id == "refresh-tickets":
            asyncio.create_task(self._refresh_tickets())
        elif button_id == "work-copilot":
            if self.selected_ticket:
                self.post_message(OpenTicketInChat(self.selected_ticket, "copilot"))
        elif button_id == "work-investigator":
            if self.selected_ticket:
                self.post_message(OpenTicketInChat(self.selected_ticket, "investigator"))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle ticket selection in the table."""
        ticket_id = event.row_key.value
        self.selected_ticket = next((t for t in self._tickets if t.id == ticket_id), None)

        # Update details panel
        if self.selected_ticket:
            self.details_panel.show_ticket(self.selected_ticket)
            self.query_one("#work-copilot", Button).disabled = False
            self.query_one("#work-investigator", Button).disabled = False
        else:
            self.details_panel.clear()
            self.query_one("#work-copilot", Button).disabled = True
            self.query_one("#work-investigator", Button).disabled = True

    async def _refresh_tickets(self) -> None:
        """Refresh the ticket list from the backend."""
        # Show loading state on button
        refresh_btn = self.query_one("#refresh-tickets", Button)
        original_label = refresh_btn.label
        refresh_btn.label = "Loading..."
        refresh_btn.disabled = True

        try:
            response = await self.client.http_client.get(
                f"{self.client.base_url}/tickets",
                params={"limit": 50},
            )
            if response.status_code == 200:
                data = response.json()
                tickets = data.get("tickets", [])
                self._tickets = [
                    TicketInfo(
                        id=t["id"],
                        title=t["title"],
                        status=t.get("status", "unknown"),
                        priority=t.get("priority", "medium"),
                        description=t.get("description", ""),
                        assigned_to=t.get("assigned_to"),
                        tags=t.get("tags", []) or t.get("labels", []),
                    )
                    for t in tickets
                ]
                self.tickets_table.update_tickets(self._tickets)
                logger.info(f"Refreshed {len(self._tickets)} tickets")
            else:
                logger.error(f"Failed to fetch tickets: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to refresh tickets: {e}")
        finally:
            # Restore button state
            refresh_btn.label = original_label
            refresh_btn.disabled = False

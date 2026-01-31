"""Pydantic models for data request tracking nodes.

These models represent data access requests and their lifecycle:
- DataRequestTicket: Tracks data access requests from users
"""

from typing import ClassVar, Optional

from pydantic import computed_field

from lineage.backends.lineage.models.base import BaseNode
from lineage.backends.types import NodeLabel


class DataRequestTicket(BaseNode):
    """Data request ticket node.

    Represents a request for data access or analysis, tracking the
    requester, justification, status, and assignment.

    The ID is typically a ticket number or UUID.
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DATA_REQUEST_TICKET

    # Core properties
    name: str  # Ticket number or title
    title: str
    description: str
    requested_data: str  # Description of requested data
    business_justification: str
    requester: str  # User who requested
    status: str  # "open", "in_progress", "completed", "rejected"
    priority: str  # "low", "medium", "high", "urgent"
    created_at: str  # ISO 8601 timestamp
    assigned_to: Optional[str] = None  # User assigned to fulfill request

    # Ticket ID (set externally or use name)
    ticket_id: str = ""

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from ticket_id or name."""
        if self.ticket_id:
            return f"ticket::{self.ticket_id}"
        return f"ticket::{self.name}"

__all__ = ["DataRequestTicket"]

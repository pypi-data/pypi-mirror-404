"""Ticket management interface for inter-agent communication.

This provides an auditable way for agents to communicate and track work.
Similar to LineageStorage pattern, this is backend-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class TicketStatus(str, Enum):
    """Ticket status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    BACKLOG = "backlog"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Ticket:
    """A ticket representing work to be done or communication between agents."""

    id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_by: str  # Agent name
    assigned_to: Optional[str] = None  # Agent name
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    comments: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ticket to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "comments": self.comments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Ticket:
        """Create ticket from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=TicketStatus(data["status"]),
            priority=TicketPriority(data["priority"]),
            created_by=data["created_by"],
            assigned_to=data.get("assigned_to"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            comments=data.get("comments", []),
        )


class TicketStorage(Protocol):
    """Abstract interface for ticket storage backends."""

    async def create_ticket(
        self,
        title: str,
        description: str,
        priority: TicketPriority,
        created_by: str,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Create a new ticket.

        Args:
            title: Short title/summary
            description: Detailed description
            priority: Ticket priority
            created_by: Agent name creating the ticket
            assigned_to: Optional agent to assign ticket to
            tags: Optional tags for categorization
            metadata: Optional additional metadata

        Returns:
            Created ticket with generated ID
        """
        ...

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID.

        Args:
            ticket_id: Ticket ID

        Returns:
            Ticket if found, None otherwise
        """
        ...

    async def update_ticket(
        self,
        ticket_id: str,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Update ticket fields.

        Args:
            ticket_id: Ticket ID
            status: New status
            priority: New priority
            assigned_to: New assignee
            tags: New tags (replaces existing)
            metadata: Metadata to merge with existing

        Returns:
            Updated ticket

        Raises:
            ValueError: If ticket not found
        """
        ...

    async def add_comment(
        self,
        ticket_id: str,
        author: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Add comment to ticket.

        Args:
            ticket_id: Ticket ID
            author: Agent name adding comment
            comment: Comment text
            metadata: Optional comment metadata

        Returns:
            Updated ticket

        Raises:
            ValueError: If ticket not found
        """
        ...

    async def list_tickets(
        self,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Ticket]:
        """List tickets with optional filtering.

        Args:
            status: Filter by status
            priority: Filter by priority
            assigned_to: Filter by assignee
            created_by: Filter by creator
            tags: Filter by tags (ticket must have all tags)
            limit: Maximum number of tickets to return

        Returns:
            List of matching tickets, sorted by updated_at DESC
        """
        ...

    def get_agent_hints(self) -> Optional[str]:
        """Get agent hints."""
        ...

    def close(self) -> None:
        """Close the storage backend."""
        ...

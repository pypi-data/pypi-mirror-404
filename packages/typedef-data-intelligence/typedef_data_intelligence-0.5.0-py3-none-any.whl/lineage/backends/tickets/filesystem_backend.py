"""Filesystem-based ticket storage implementation."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .protocol import Ticket, TicketPriority, TicketStatus, TicketStorage


class FilesystemTicketStorage(TicketStorage):
    """Filesystem-based ticket storage using JSON files."""

    def __init__(self, base_path: str = "./tickets"):
        """Initialize filesystem ticket storage.

        Args:
            base_path: Base directory for ticket storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _ticket_path(self, ticket_id: str) -> Path:
        """Get path to ticket file."""
        return self.base_path / f"{ticket_id}.json"

    def _save_ticket(self, ticket: Ticket) -> None:
        """Save ticket to filesystem."""
        ticket_path = self._ticket_path(ticket.id)
        with open(ticket_path, "w") as f:
            json.dump(ticket.to_dict(), f, indent=2)

    def _load_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Load ticket from filesystem."""
        ticket_path = self._ticket_path(ticket_id)
        if not ticket_path.exists():
            return None

        with open(ticket_path, "r") as f:
            data = json.load(f)
        return Ticket.from_dict(data)

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
        """Create a new ticket."""
        ticket_id = str(uuid.uuid4())[:8]  # Short ID
        now = datetime.now(timezone.utc)

        ticket = Ticket(
            id=ticket_id,
            title=title,
            description=description,
            status=TicketStatus.OPEN,
            priority=priority,
            created_by=created_by,
            assigned_to=assigned_to,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            metadata=metadata or {},
            comments=[],
        )

        self._save_ticket(ticket)
        return ticket

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID."""
        return self._load_ticket(ticket_id)

    async def update_ticket(
        self,
        ticket_id: str,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Update ticket fields."""
        ticket = self._load_ticket(ticket_id)
        if ticket is None:
            raise ValueError(f"Ticket not found: {ticket_id}")

        # Update fields
        if status is not None:
            ticket.status = status
            if status == TicketStatus.COMPLETED:
                ticket.completed_at = datetime.now(timezone.utc)

        if priority is not None:
            ticket.priority = priority

        if assigned_to is not None:
            ticket.assigned_to = assigned_to

        if tags is not None:
            ticket.tags = tags

        if metadata is not None:
            ticket.metadata.update(metadata)

        ticket.updated_at = datetime.now(timezone.utc)
        self._save_ticket(ticket)
        return ticket

    async def add_comment(
        self,
        ticket_id: str,
        author: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Add comment to ticket."""
        ticket = self._load_ticket(ticket_id)
        if ticket is None:
            raise ValueError(f"Ticket not found: {ticket_id}")

        comment_data = {
            "author": author,
            "comment": comment,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

        ticket.comments.append(comment_data)
        ticket.updated_at = datetime.now(timezone.utc)
        self._save_ticket(ticket)
        return ticket

    async def list_tickets(
        self,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Ticket]:
        """List tickets with optional filtering."""
        tickets = []

        # Load all tickets
        for ticket_path in self.base_path.glob("*.json"):
            with open(ticket_path, "r") as f:
                data = json.load(f)
            ticket = Ticket.from_dict(data)

            # Apply filters
            if status is not None and ticket.status != status:
                continue
            if priority is not None and ticket.priority != priority:
                continue
            if assigned_to is not None and ticket.assigned_to != assigned_to:
                continue
            if created_by is not None and ticket.created_by != created_by:
                continue
            if tags is not None and not all(tag in ticket.tags for tag in tags):
                continue

            tickets.append(ticket)

        # Sort by updated_at DESC
        tickets.sort(key=lambda t: t.updated_at, reverse=True)

        # Apply limit
        if limit is not None:
            tickets = tickets[:limit]

        return tickets

    def get_agent_hints(self):
        """Get agent hints for the filesystem backend."""
        return None

    def close(self) -> None:
        """Close the storage backend (no-op for filesystem)."""
        pass

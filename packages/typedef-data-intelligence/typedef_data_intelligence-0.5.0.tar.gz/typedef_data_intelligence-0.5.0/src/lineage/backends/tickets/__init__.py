"""Ticket management system for inter-agent communication."""

from .protocol import TicketStorage, Ticket, TicketStatus, TicketPriority
from .filesystem_backend import FilesystemTicketStorage
from .linear_backend import LinearTicketStorage

__all__ = [
    "TicketStorage",
    "Ticket",
    "TicketStatus",
    "TicketPriority",
    "FilesystemTicketStorage",
    "LinearTicketStorage",
]

"""
MCP (Memory / Context / Plugin) Integration Layer
"""

from .sqlite_client import SQLiteClient
from .ticket_client import TicketClient

__all__ = ["SQLiteClient", "TicketClient"]

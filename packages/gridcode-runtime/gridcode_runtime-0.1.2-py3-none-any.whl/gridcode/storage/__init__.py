"""Storage module for GridCode Runtime.

This module provides persistent storage backends for session state,
conversation history, and other runtime data.

Usage:
    from gridcode.storage import SQLiteStorage

    storage = SQLiteStorage(Path("sessions.db"))
    await storage.save_context(session_id, context)
    context = await storage.load_context(session_id)
"""

from gridcode.storage.base import StorageBackend
from gridcode.storage.sqlite import SQLiteStorage

__all__ = ["StorageBackend", "SQLiteStorage"]

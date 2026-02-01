"""SQLite-based storage backend for GridCode Runtime.

This module provides a persistent storage backend using SQLite,
suitable for single-node deployments and local development.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite
from loguru import logger

from gridcode.core.context import ExecutionContext
from gridcode.storage.base import SessionMetadata, StorageBackend, StorageError


class SQLiteStorage(StorageBackend):
    """SQLite-based storage backend.

    This backend stores session contexts in a SQLite database file,
    providing persistence across runtime restarts.

    Example:
        storage = SQLiteStorage(Path("sessions.db"))
        await storage.initialize()

        # Save a context
        await storage.save_context("session-1", context)

        # Load it back
        context = await storage.load_context("session-1")

        # Clean up
        await storage.close()
    """

    def __init__(self, db_path: Path):
        """Initialize the SQLite storage backend.

        Args:
            db_path: Path to the SQLite database file.
                    Will be created if it doesn't exist.
        """
        self.db_path = db_path
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database schema.

        This method creates the sessions table if it doesn't exist.
        Call this before using other methods.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    context_data TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
                ON sessions(updated_at DESC)
            """)
            await db.commit()

        self._initialized = True
        logger.debug(f"SQLiteStorage initialized at {self.db_path}")

    async def _ensure_initialized(self) -> None:
        """Ensure the database is initialized."""
        if not self._initialized:
            await self.initialize()

    async def save_context(
        self,
        session_id: str,
        context: ExecutionContext,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save an execution context to the database.

        Args:
            session_id: Unique identifier for the session
            context: The ExecutionContext to save
            metadata: Optional additional metadata to store
        """
        await self._ensure_initialized()

        try:
            context_data = context.model_dump_json()
            metadata_json = json.dumps(metadata) if metadata else None

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO sessions (session_id, context_data, metadata, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(session_id) DO UPDATE SET
                        context_data = excluded.context_data,
                        metadata = excluded.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id, context_data, metadata_json),
                )
                await db.commit()

            logger.debug(f"Saved context for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save context for session {session_id}: {e}")
            raise StorageError(f"Failed to save context: {e}") from e

    async def load_context(self, session_id: str) -> ExecutionContext | None:
        """Load an execution context from the database.

        Args:
            session_id: Unique identifier for the session

        Returns:
            The ExecutionContext if found, None otherwise
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT context_data FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                row = await cursor.fetchone()

                if row:
                    context = ExecutionContext.model_validate_json(row[0])
                    logger.debug(f"Loaded context for session: {session_id}")
                    return context

                logger.debug(f"No context found for session: {session_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to load context for session {session_id}: {e}")
            raise StorageError(f"Failed to load context: {e}") from e

    async def delete_context(self, session_id: str) -> bool:
        """Delete a session from the database.

        Args:
            session_id: Unique identifier for the session

        Returns:
            True if the session was deleted, False if it didn't exist
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                await db.commit()
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.debug(f"Deleted session: {session_id}")
                else:
                    logger.debug(f"Session not found for deletion: {session_id}")

                return deleted
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise StorageError(f"Failed to delete context: {e}") from e

    async def list_sessions(self) -> list[SessionMetadata]:
        """List all stored sessions.

        Returns:
            List of SessionMetadata for all stored sessions,
            sorted by updated_at descending (most recent first)
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT session_id, metadata, created_at, updated_at
                    FROM sessions
                    ORDER BY updated_at DESC
                    """)
                rows = await cursor.fetchall()

                sessions = []
                for row in rows:
                    session_id, metadata_json, created_at, updated_at = row
                    metadata = json.loads(metadata_json) if metadata_json else {}

                    sessions.append(
                        SessionMetadata(
                            session_id=session_id,
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            metadata=metadata,
                        )
                    )

                logger.debug(f"Listed {len(sessions)} sessions")
                return sessions
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise StorageError(f"Failed to list sessions: {e}") from e

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists in the database.

        Args:
            session_id: Unique identifier for the session

        Returns:
            True if the session exists, False otherwise
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT 1 FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                row = await cursor.fetchone()
                return row is not None
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}")
            raise StorageError(f"Failed to check session existence: {e}") from e

    async def get_session_metadata(self, session_id: str) -> SessionMetadata | None:
        """Get metadata for a specific session.

        Args:
            session_id: Unique identifier for the session

        Returns:
            SessionMetadata if found, None otherwise
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT metadata, created_at, updated_at
                    FROM sessions
                    WHERE session_id = ?
                    """,
                    (session_id,),
                )
                row = await cursor.fetchone()

                if row:
                    metadata_json, created_at, updated_at = row
                    metadata = json.loads(metadata_json) if metadata_json else {}

                    return SessionMetadata(
                        session_id=session_id,
                        created_at=datetime.fromisoformat(created_at),
                        updated_at=datetime.fromisoformat(updated_at),
                        metadata=metadata,
                    )

                return None
        except Exception as e:
            logger.error(f"Failed to get session metadata {session_id}: {e}")
            raise StorageError(f"Failed to get session metadata: {e}") from e

    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """Remove sessions older than the specified number of days.

        Args:
            days: Number of days to keep sessions (default 30)

        Returns:
            Number of sessions deleted
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    DELETE FROM sessions
                    WHERE updated_at < datetime('now', '-' || ? || ' days')
                    """,
                    (days,),
                )
                await db.commit()
                deleted = cursor.rowcount

                logger.info(f"Cleaned up {deleted} old sessions (older than {days} days)")
                return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            raise StorageError(f"Failed to cleanup old sessions: {e}") from e

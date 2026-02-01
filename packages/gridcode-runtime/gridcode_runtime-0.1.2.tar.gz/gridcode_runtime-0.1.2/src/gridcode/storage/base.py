"""Abstract base class for storage backends.

This module defines the interface that all storage backends must implement.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from gridcode.core.context import ExecutionContext


class SessionMetadata(BaseModel):
    """Metadata about a stored session."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = {}


class StorageBackend(ABC):
    """Abstract base class for storage backends.

    All storage implementations must inherit from this class and implement
    the required methods.

    Example:
        class MyStorage(StorageBackend):
            async def save_context(self, session_id, context):
                # Implementation
                pass

            async def load_context(self, session_id):
                # Implementation
                pass

            # ... other methods
    """

    @abstractmethod
    async def save_context(
        self,
        session_id: str,
        context: "ExecutionContext",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save an execution context to storage.

        Args:
            session_id: Unique identifier for the session
            context: The ExecutionContext to save
            metadata: Optional additional metadata to store

        Raises:
            StorageError: If the save operation fails
        """
        pass

    @abstractmethod
    async def load_context(self, session_id: str) -> "ExecutionContext | None":
        """Load an execution context from storage.

        Args:
            session_id: Unique identifier for the session

        Returns:
            The ExecutionContext if found, None otherwise

        Raises:
            StorageError: If the load operation fails
        """
        pass

    @abstractmethod
    async def delete_context(self, session_id: str) -> bool:
        """Delete a session from storage.

        Args:
            session_id: Unique identifier for the session

        Returns:
            True if the session was deleted, False if it didn't exist

        Raises:
            StorageError: If the delete operation fails
        """
        pass

    @abstractmethod
    async def list_sessions(self) -> list[SessionMetadata]:
        """List all stored sessions.

        Returns:
            List of SessionMetadata for all stored sessions

        Raises:
            StorageError: If the list operation fails
        """
        pass

    @abstractmethod
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists in storage.

        Args:
            session_id: Unique identifier for the session

        Returns:
            True if the session exists, False otherwise
        """
        pass

    async def update_metadata(
        self,
        session_id: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Update metadata for an existing session.

        Args:
            session_id: Unique identifier for the session
            metadata: Metadata to merge with existing metadata

        Returns:
            True if the session was updated, False if it didn't exist

        Note:
            Default implementation loads and saves the full context.
            Backends may override with more efficient implementations.
        """
        context = await self.load_context(session_id)
        if context is None:
            return False

        # Merge metadata
        existing_metadata = context.metadata or {}
        existing_metadata.update(metadata)
        context.metadata = existing_metadata

        await self.save_context(session_id, context, metadata)
        return True


class StorageError(Exception):
    """Exception raised for storage operation errors."""

    pass

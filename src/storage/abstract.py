"""Abstract storage interface for activity and session data."""

from abc import ABC, abstractmethod
from typing import Optional

from src.models import ActivitySnapshot, Session


class ActivityStorage(ABC):
    """Abstract interface for persisting activity and session data.

    Implementations of this interface handle all database operations
    for storing activities and managing sessions. The storage maintains
    session context state to automatically tag activities.

    Storage is a pure data layer with no business logic - it saves and
    retrieves data as instructed by the coordinator.
    """

    @abstractmethod
    def set_session_context(self, session_id: Optional[str]) -> None:
        """Set the current session context for activity tracking.

        Args:
            session_id: The session ID to tag activities with, or None for idle mode.
        """
        pass

    @abstractmethod
    def save_activity(self, snapshot: ActivitySnapshot) -> None:
        """Save an activity snapshot with the current session context.

        Args:
            snapshot: The activity snapshot to save.
        """
        pass

    @abstractmethod
    def save_session(self, session: Session) -> None:
        """Persist a new session to storage.

        Args:
            session: The session to save.
        """
        pass

    @abstractmethod
    def update_session(self, session: Session) -> None:
        """Update an existing session in storage.

        Args:
            session: The session with updated fields.

        Raises:
            KeyError: If session.id doesn't exist.
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Session:
        """Retrieve a session by ID.

        Args:
            session_id: The session ID to retrieve.

        Returns:
            The Session object.

        Raises:
            KeyError: If session_id doesn't exist.
        """
        pass

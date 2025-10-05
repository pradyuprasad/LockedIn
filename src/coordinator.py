"""Coordinator for managing focus sessions and activity tracking."""

import hashlib
import re
import threading
import time
from datetime import datetime
from typing import Optional

from src.logging import get_logger
from src.models import Session
from src.polling.abstract import ActivityPoller
from src.storage.abstract import ActivityStorage

logger = get_logger(__name__)


class Coordinator:
    """Coordinates activity polling and session management.

    The coordinator runs a background polling loop that continuously
    captures user activity. It manages session lifecycle (idle vs focus mode)
    and orchestrates the poller and storage components.

    Args:
        poller: ActivityPoller implementation to capture activity.
        storage: ActivityStorage implementation to persist data.
        interval: Polling interval in seconds. Defaults to 1.0.
    """

    def __init__(
        self,
        poller: ActivityPoller,
        storage: ActivityStorage,
        interval: float = 1.0
    ):
        """Initialize coordinator and start background polling.

        Args:
            poller: ActivityPoller implementation.
            storage: ActivityStorage implementation.
            interval: Polling interval in seconds.
        """
        self.poller = poller
        self.storage = storage
        self.interval = interval
        self.current_session_id: Optional[str] = None

        # Start background polling immediately
        logger.info("Starting background activity polling")
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()

    def _poll_loop(self) -> None:
        """Background polling loop that runs continuously.

        Captures activity snapshots at regular intervals and saves them
        to storage with the current session context.
        """
        while True:
            try:
                snapshot = self.poller.poll_once()
                self.storage.save_activity(snapshot)
            except Exception as e:
                logger.error(f"Error during polling: {e}")

            time.sleep(self.interval)

    def start_session(self, task: str, goal: str) -> Session:
        """Create and start a new focus session.

        Generates a human-readable session ID from the task, creates
        the session in storage, and enters focus mode.

        Args:
            task: Specific thing being worked on.
            goal: Bigger context/motivation.

        Returns:
            The created Session.
        """
        session_id = self._generate_session_id(task)
        session = Session(
            id=session_id,
            task=task,
            goal=goal,
            start_time=datetime.now(),
            end_time=None
        )

        self.storage.save_session(session)
        self.storage.set_session_context(session_id)
        self.current_session_id = session_id

        logger.info(f"Started session: {session_id} - {task}")

        return session

    def end_session(self) -> Session:
        """End the current focus session and return to idle mode.

        Returns:
            The ended Session with end_time set.

        Raises:
            RuntimeError: If no active session to end.
        """
        if self.current_session_id is None:
            raise RuntimeError("No active session to end")

        session = self.storage.get_session(self.current_session_id)
        session.end_time = datetime.now()

        self.storage.update_session(session)
        self.storage.set_session_context(None)

        logger.info(f"Ended session: {self.current_session_id}")

        self.current_session_id = None

        return session

    def get_current_session(self) -> Optional[Session]:
        """Get the currently active session, if any.

        Returns:
            The current Session, or None if in idle mode.
        """
        if self.current_session_id is None:
            return None
        return self.storage.get_session(self.current_session_id)

    def _generate_session_id(self, task: str) -> str:
        """Generate a human-readable session ID from the task.

        Creates an ID like: fix-auth-bug-7a3c2f

        Args:
            task: The task description.

        Returns:
            Human-readable session ID.
        """
        # Sanitize task: lowercase, alphanumeric + spaces only
        sanitized = re.sub(r'[^a-z0-9\s]', '', task.lower())
        # Convert spaces to dashes, collapse multiple dashes
        slug = re.sub(r'\s+', '-', sanitized).strip('-')
        # Truncate to 30 chars
        slug = slug[:30].rstrip('-')

        # Generate short hash for uniqueness
        hash_obj = hashlib.sha256(f"{task}{datetime.now().isoformat()}".encode())
        short_hash = hash_obj.hexdigest()[:6]

        return f"{slug}-{short_hash}"

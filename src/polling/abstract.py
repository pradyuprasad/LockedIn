"""Activity polling interface.

This module defines the protocol that all activity pollers must implement.
"""

from typing import Protocol
from src.models import ActivitySnapshot


class ActivityPoller(Protocol):
    """Polls for current user activity.

    The poller is a stateless worker that captures a single snapshot
    of user activity when called. The caller is responsible for
    timing and persistence.
    """

    def poll_once(self) -> ActivitySnapshot:
        """Capture and return current user activity.

        Returns:
            ActivitySnapshot containing current app, window, URL, etc.
        """
        ...

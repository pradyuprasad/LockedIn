"""Module for common models."""

from datetime import datetime
from pydantic import BaseModel


class ActivitySnapshot(BaseModel):
    """A single point-in-time capture of user activity.

    Attributes:
        timestamp: When this activity was captured.
        app_name: Name of the active application (e.g., "Google Chrome", "VSCode").
        window_title: Title of the active window.
        url: The current URL if app is a recognized browser, None otherwise.
        domain: Extracted domain from URL for grouping/metrics, None if no URL.
    """

    timestamp: datetime
    app_name: str
    window_title: str
    url: str | None = None
    domain: str | None = None


class Session(BaseModel):
    """A focus session with declared intent.

    Attributes:
        id: Unique identifier for this session.
        task: Specific thing being worked on (e.g., "Fix authentication bug").
        goal: Bigger context/motivation (e.g., "Ship v2 by month end").
        start_time: When the session began.
        end_time: When the session ended, None if still active.
    """

    id: str
    task: str
    goal: str
    start_time: datetime
    end_time: datetime | None = None

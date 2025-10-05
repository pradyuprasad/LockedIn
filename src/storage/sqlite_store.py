"""SQLite implementation of ActivityStorage."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import DB_PATH
from src.models import ActivitySnapshot, Session
from src.storage.abstract import ActivityStorage


class SQLiteStorage(ActivityStorage):
    """SQLite-based storage for activities and sessions.

    This implementation stores all data in a local SQLite database
    and maintains session context state for activity tagging.

    Args:
        db_path: Path to the SQLite database file. Defaults to config.DB_PATH.

    Raises:
        FileNotFoundError: If database doesn't exist. Run scripts/setup.py first.
    """

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize SQLite storage connection.

        Args:
            db_path: Path to the SQLite database file.

        Raises:
            FileNotFoundError: If database file doesn't exist.
        """
        if not Path(db_path).exists():
            raise FileNotFoundError(
                f"Database not found at {db_path}. "
                "Please run 'uv run scripts/setup.py' first."
            )

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.current_session_id: Optional[str] = None

    def set_session_context(self, session_id: Optional[str]) -> None:
        """Set the current session context for activity tracking.

        Args:
            session_id: The session ID to tag activities with, or None for idle mode.
        """
        self.current_session_id = session_id

    def save_activity(self, snapshot: ActivitySnapshot) -> None:
        """Save an activity snapshot with the current session context.

        Args:
            snapshot: The activity snapshot to save.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO activities (session_id, timestamp, app_name, window_title, url, domain)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.current_session_id,
                snapshot.timestamp.isoformat(),
                snapshot.app_name,
                snapshot.window_title,
                snapshot.url,
                snapshot.domain,
            ),
        )
        self.conn.commit()

    def save_session(self, session: Session) -> None:
        """Persist a new session to storage.

        Args:
            session: The session to save.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (id, task, goal, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.task,
                session.goal,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
            ),
        )
        self.conn.commit()

    def update_session(self, session: Session) -> None:
        """Update an existing session in storage.

        Args:
            session: The session with updated fields.

        Raises:
            KeyError: If session.id doesn't exist.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE sessions
            SET task = ?, goal = ?, start_time = ?, end_time = ?
            WHERE id = ?
            """,
            (
                session.task,
                session.goal,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
                session.id,
            ),
        )

        if cursor.rowcount == 0:
            raise KeyError(f"Session not found: {session.id}")

        self.conn.commit()

    def get_session(self, session_id: str) -> Session:
        """Retrieve a session by ID.

        Args:
            session_id: The session ID to retrieve.

        Returns:
            The Session object.

        Raises:
            KeyError: If session_id doesn't exist.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, task, goal, start_time, end_time
            FROM sessions
            WHERE id = ?
            """,
            (session_id,),
        )

        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Session not found: {session_id}")

        return Session(
            id=row["id"],
            task=row["task"],
            goal=row["goal"],
            start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
        )

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def get_session_activities(self, session_id: str) -> list[ActivitySnapshot]:
        """Retrieve all activities for a given session.

        Args:
            session_id: The session ID to retrieve activities for.

        Returns:
            List of ActivitySnapshot objects, ordered by timestamp.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, app_name, window_title, url, domain
            FROM activities
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        )

        activities = []
        for row in cursor.fetchall():
            activities.append(
                ActivitySnapshot(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    app_name=row["app_name"],
                    window_title=row["window_title"],
                    url=row["url"],
                    domain=row["domain"],
                )
            )

        return activities

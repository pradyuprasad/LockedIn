import time
from typing import Optional, Dict, Any
from database_manager import DatabaseManager
from .utils import format_elapsed_time


class SessionManager:
    """Manages tracking sessions"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.current_session: Optional[str] = None
        self.session_start_time: Optional[float] = None
        self.overall_start_time: float = time.time()

    def start_session(self, name: str) -> None:
        """Start a new session with the given name."""
        self.current_session = name
        self.session_start_time = time.time()
        print(f"New session started: {name}")

    def stop_session(self) -> None:
        """Stop the current session."""
        if self.current_session:
            print(f"Session '{self.current_session}' stopped.")
            self.current_session = None
            self.session_start_time = None
        else:
            print("No active session to stop.")

    def get_session_info(self) -> Dict[str, Any]:
        """Return information about the current session."""
        info = {
            "current_session": self.current_session,
            "session_start_time": self.session_start_time,
            "overall_start_time": self.overall_start_time,
            "elapsed_time_overall": int(time.time() - self.overall_start_time),
            "elapsed_time_session": None,
            "session_start_str": None,
            "formatted_elapsed_time_overall": format_elapsed_time(
                int(time.time() - self.overall_start_time)
            ),
        }

        if self.session_start_time:
            elapsed_time_session = int(time.time() - self.session_start_time)
            info["elapsed_time_session"] = elapsed_time_session
            info["session_start_str"] = time.strftime(
                "%H:%M %d/%m/%Y", time.localtime(self.session_start_time)
            )
            info["formatted_elapsed_time_session"] = format_elapsed_time(
                elapsed_time_session
            )

        return info

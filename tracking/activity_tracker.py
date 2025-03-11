from typing import Tuple, Optional
from AppKit import NSWorkspace
from database_manager import DatabaseManager
from .utils import get_browser_info, get_window_title

class ActivityTracker:
    """Core activity tracking functionality"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_active_window_info(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Retrieve the active window's details based on the application."""
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            app_name = active_app["NSApplicationName"]

            # Skip tracking when computer is idle
            if app_name == "loginwindow":
                return "Idle", "Computer Off", None

            if app_name in ["Safari", "Google Chrome", "Firefox", "Brave Browser"]:
                url, title = get_browser_info(app_name)
                return app_name, title.strip() if title else "No title", url.strip() if url else None
            else:
                window_title = get_window_title(app_name)
                return app_name, window_title, None
        except Exception as e:
            print(f"Error getting window info: {e}")
            return None, None, None
    
    def track_activity(self, timestamp: str, session_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Track a single activity and store it in the database."""
        app_name, window_title, url = self.get_active_window_info()
        
        if app_name:
            self.db_manager.insert_activity(timestamp, app_name, window_title, url, session_name)
        
        return app_name, window_title, url

"""macOS-specific activity poller implementation using AppleScript.

This module provides a concrete implementation of the ActivityPoller protocol
that uses AppleScript via subprocess calls to capture user activity on macOS.
"""

import subprocess
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

from src.models import ActivitySnapshot


class Browser(Enum):
    """Supported browsers for URL extraction."""
    CHROME = "Google Chrome"
    SAFARI = "Safari"
    FIREFOX = "Firefox"
    ARC = "Arc"
    BRAVE = "Brave Browser"


class MacOSPoller:
    """Activity poller for macOS that uses AppleScript to capture activity.

    This poller creates a new subprocess for each AppleScript call to gather
    information about the active application, window title, and browser URL.
    """

    def poll_once(self) -> ActivitySnapshot:
        """Capture and return current user activity on macOS.

        Creates subprocess calls to AppleScript to determine:
        - Active application name
        - Active window title
        - Current URL (if application is a recognized browser)
        - Domain extracted from URL

        Returns:
            ActivitySnapshot containing current app, window, URL, and domain.
        """
        app_name = self._get_active_app()
        window_title = self._get_window_title()
        url = self._get_browser_url(app_name) if self._is_browser(app_name) else None
        domain = self._extract_domain(url) if url else None

        return ActivitySnapshot(
            timestamp=datetime.now(),
            app_name=app_name,
            window_title=window_title,
            url=url,
            domain=domain
        )

    def _get_active_app(self) -> str:
        """Get the name of the currently active application.

        Returns:
            Name of the active application (e.g., "Google Chrome").
        """
        script = '''
            tell application "System Events"
                name of first application process whose frontmost is true
            end tell
        '''
        return self._run_applescript(script)

    def _get_window_title(self) -> str:
        """Get the title of the currently active window.

        Returns:
            Title of the active window.
        """
        script = '''
            tell application "System Events"
                tell (first application process whose frontmost is true)
                    name of window 1
                end tell
            end tell
        '''
        return self._run_applescript(script)

    def _is_browser(self, app_name: str) -> bool:
        """Check if the given application is a recognized browser.

        Args:
            app_name: Name of the application to check.

        Returns:
            True if app is a recognized browser, False otherwise.
        """
        return app_name in {browser.value for browser in Browser}

    def _get_browser_url(self, app_name: str) -> str | None:
        """Get the current URL from the active browser tab.

        Args:
            app_name: Name of the browser application.

        Returns:
            Current URL if available, None if unable to retrieve.
        """
        # Find matching browser enum
        browser = None
        for b in Browser:
            if b.value == app_name:
                browser = b
                break

        if browser is None:
            return None

        match browser:
            case Browser.CHROME | Browser.ARC | Browser.BRAVE:
                script = f'''
                    tell application "{app_name}"
                        URL of active tab of front window
                    end tell
                '''
            case Browser.SAFARI:
                script = '''
                    tell application "Safari"
                        URL of current tab of front window
                    end tell
                '''
            case Browser.FIREFOX:
                # Firefox AppleScript support is limited
                return None

        try:
            return self._run_applescript(script)
        except subprocess.CalledProcessError:
            return None

    def _extract_domain(self, url: str) -> str:
        """Extract domain from a URL.

        Args:
            url: Full URL string.

        Returns:
            Domain portion of the URL (e.g., "github.com").
        """
        parsed = urlparse(url)
        return parsed.netloc

    def _run_applescript(self, script: str) -> str:
        """Execute an AppleScript and return its output.

        Creates a new subprocess to run osascript with the given script.

        Args:
            script: AppleScript code to execute.

        Returns:
            Stripped output from the AppleScript execution.

        Raises:
            subprocess.CalledProcessError: If the AppleScript execution fails.
        """
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

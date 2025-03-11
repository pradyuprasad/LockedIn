import re
import subprocess
from urllib.parse import urlparse
from typing import Tuple, Optional

def format_elapsed_time(seconds: int) -> str:
    """Convert seconds into a human-readable format: days, hours, minutes, seconds."""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    elapsed_time_str = []
    if days > 0:
        elapsed_time_str.append(f"{days}d")
    if hours > 0:
        elapsed_time_str.append(f"{hours}h")
    if minutes > 0:
        elapsed_time_str.append(f"{minutes}m")
    elapsed_time_str.append(f"{seconds}s")

    return " ".join(elapsed_time_str)

def extract_domain(url: str) -> Optional[str]:
    """Extract the domain name from a URL."""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove 'www.' prefix if it exists
        domain = re.sub(r"^www\.", "", domain)
        return domain
    except Exception:
        return None

def run_applescript(script: str) -> Optional[str]:
    """Run an AppleScript command and return the result."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_browser_info(app_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Get the current tab's URL and title for supported browsers."""
    script = f'''
    tell application "{app_name}"
        set currentTab to active tab of front window
        return (URL of currentTab) & "|" & (name of currentTab)
    end tell
    '''
    result = run_applescript(script)
    if result:
        return result.split("|", 1)
    return None, None

def get_window_title(app_name: str) -> str:
    """Get the window title for non-browser applications."""
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                return name of front window
            on error
                return "No window title available"
            end try
        end tell
    end tell
    '''
    return run_applescript(script) or "No window title available"

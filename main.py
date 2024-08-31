import select
import sys
import time
import sqlite3
import subprocess
from AppKit import NSWorkspace
import click

def run_applescript(script):
    """Run an AppleScript command and return the result."""
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_browser_info(app_name):
    """Get the current tab's URL and title for supported browsers."""
    script = f'''
    tell application "{app_name}"
        set currentTab to active tab of front window
        return (URL of currentTab) & "|" & (name of currentTab)
    end tell
    '''
    result = run_applescript(script)
    if result:
        return result.split('|', 1)
    return None, None

def get_window_title(app_name):
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

def get_active_window_info():
    """Retrieve the active window's details based on the application."""
    try:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.activeApplication()
        app_name = active_app["NSApplicationName"]
        if app_name in ["Safari", "Google Chrome", "Firefox", "Brave Browser"]:
            url, title = get_browser_info(app_name)
            return app_name, title.strip(), url.strip()
        else:
            window_title = get_window_title(app_name)
            return app_name, window_title, None
    except Exception as e:
        print(f"Error getting window info: {e}")
        return None, None, None

def insert_activity(conn, timestamp, app_name, window_title, url, session_name):
    """Insert a record of the activity into the database."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO activities (timestamp, app_name, window_title, url, session)
    VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, app_name, window_title, url, session_name))
    conn.commit()
    print(f"Inserted {timestamp}, {app_name}, {window_title}, {url}, {session_name}")

@click.group()
def cli():
    """CLI application for tracking window activities."""
    pass

@cli.command()
def start():
    """Start tracking activities."""
    conn = sqlite3.connect('tracker.db')
    current_session = None
    print("Activity tracking started.")
    print("Use 'stop' to stop tracking.")

    try:
        while True:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            app_name, window_title, url = get_active_window_info()

            if app_name:
                insert_activity(conn, current_time, app_name, window_title, url, current_session)
            else:
                print(f"{current_time}: Failed to get window info. Retrying...")

            # Check for user input (non-blocking)
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                user_input = sys.stdin.readline().strip().lower()
                if user_input == 'n':
                    current_session = input("Enter new session name: ")
                    print(f"New session started: {current_session}")
                elif user_input == 's':
                    if current_session:
                        print(f"Session '{current_session}' stopped.")
                        current_session = None
                    else:
                        print("No active session to stop.")
                else:
                    print("Invalid command. Use 'n' for new session, 's' to stop session")

            time.sleep(0.9)
    except KeyboardInterrupt:
        print("\nTracking stopped.")
    finally:
        conn.close()

@cli.command()
def stop():
    """Stop tracking activities."""
    # This command would be used to stop tracking
    # You might want to implement functionality to terminate the process or manage sessions.
    print("Stopping tracking is not yet implemented.")

if __name__ == "__main__":
    cli()

import time
import sqlite3
from AppKit import NSWorkspace
import subprocess
import select
import sys

def run_applescript(script):
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_active_window_info():
    try:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.activeApplication()
        app_name = active_app["NSApplicationName"]
        if app_name in ["Safari", "Google Chrome", "Firefox", "Brave Browser"]:
            script = f'''
            tell application "{app_name}"
                set currentTab to active tab of front window
                return (URL of currentTab) & "|" & (name of currentTab)
            end tell
            '''
            result = run_applescript(script)
            if result:
                url, title = result.split('|', 1)
                return app_name, title.strip(), url.strip()
        else:
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
            window_title = run_applescript(script) or "No window title available"
            return app_name, window_title, None
    except Exception as e:
        print(f"Error getting window info: {e}")
        return None
    return None  # If we get here, something unexpected happened

def insert_activity(conn, timestamp, app_name, window_title, url, session_name):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO activities (timestamp, app_name, window_title, url, session)
    VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, app_name, window_title, url, session_name))
    conn.commit()
    print(f"inserted {timestamp}, {app_name}, {window_title}, {url}, {session_name}")

def main():
    current_session = None
    conn = sqlite3.connect('tracker.db')
    
    print("Activity tracking started. Use the following commands:")
    print("n: Start a new session")
    print("s: Stop the current session")
    
    try:
        while True:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            window_info = get_active_window_info()
            
            if window_info is None:
                print(f"{current_time}: Failed to get window info. Retrying...")
            else:
                app_name, window_title, url = window_info
                insert_activity(conn, current_time, app_name, window_title, url, current_session)
            
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
            
            time.sleep(.9)  # Sleep for 0.9 seconds to account for processing time
            
    except KeyboardInterrupt:
        print("\nTracking stopped.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

import time
import sqlite3
from AppKit import NSWorkspace
import subprocess

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

def insert_activity(conn, timestamp, app_name, window_title, url):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO activities (timestamp, app_name, window_title, url)
    VALUES (?, ?, ?, ?)
    ''', (timestamp, app_name, window_title, url))
    conn.commit()
    print(f"inserted {timestamp}, {app_name}, {window_title}, {url}")

def main():
    conn = sqlite3.connect('tracker.db')
    
    last_app_name = None
    last_window_title = None
    last_url = None
    last_insert_time = None
    
    try:
        while True:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            window_info = get_active_window_info()
            
            if window_info is None:
                print("Failed to get window info. Retrying in 1 second...")
                time.sleep(1)
                continue
            
            app_name, window_title, url = window_info
            
            if (app_name != last_app_name or 
                window_title != last_window_title or 
                url != last_url or 
                (last_insert_time and (time.time() - last_insert_time) >= 1)):  # Force update every 5 minutes
                
                insert_activity(conn, current_time, app_name, window_title, url)
                
                last_app_name = app_name
                last_window_title = window_title
                last_url = url
                last_insert_time = time.time()
            
            time.sleep(1)  # Check every second
            
    except KeyboardInterrupt:
        print("\nTracking stopped.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
import time
import subprocess
from AppKit import NSWorkspace
import sqlite3

def run_applescript(script):
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_active_window_info():
    workspace = NSWorkspace.sharedWorkspace()
    active_app = workspace.activeApplication()
    app_name = active_app["NSApplicationName"]

    if app_name in ["Safari", "Google Chrome", "Firefox", "Brave Browser"]:
        if app_name == "Safari":
            script = '''
            tell application "Safari"
                set currentTab to current tab of front window
                return (URL of currentTab) & "|" & (name of currentTab)
            end tell
            '''
        elif app_name in ["Google Chrome", "Brave Browser"]:
            script = f'''
            tell application "{app_name}"
                set activeTab to active tab of front window
                return (URL of activeTab) & "|" & (title of activeTab)
            end tell
            '''
        elif app_name == "Firefox":
            script = '''
            tell application "Firefox"
                set windowInfo to properties of window 1
                set tabInfo to properties of active tab of window 1
                return (URL of tabInfo) & "|" & (title of tabInfo)
            end tell
            '''
        
        result = run_applescript(script)
        if result:
            url, title = result.split('|', 1)
            return app_name, title.strip(), url.strip()
        else:
            return app_name, "Unable to retrieve title", "Unable to retrieve URL"
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

def create_database():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        app_name TEXT NOT NULL,
        window_title TEXT,
        url TEXT
    )
    ''')

    conn.commit()
    return conn

def insert_activity(conn, app_name, window_title, url):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO activities (timestamp, app_name, window_title, url)
    VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
    ''', (app_name, window_title, url))
    conn.commit()

def main():
    print("Window and URL Tracker (including Brave)")
    print("Press Ctrl+C to exit")
    print("---------------------")

    conn = create_database()

    try:
        while True:
            app_name, window_title, url = get_active_window_info()
            print(f"{app_name} - Title: {window_title}, URL: {url}")
            insert_activity(conn, app_name, window_title, url)
            time.sleep(1)  # Wait for 1 second before the next insert
    except KeyboardInterrupt:
        print("\nTracking stopped.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

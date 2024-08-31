from collections import defaultdict
import re
import select
import sys
import time
import sqlite3
import subprocess
from urllib.parse import urlparse
from AppKit import NSWorkspace
import click

activity_duration = defaultdict(int)

def format_elapsed_time(seconds):
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
    
    return ' '.join(elapsed_time_str)

def extract_domain(url):
    """Extract the domain name from a URL."""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove 'www.' prefix if it exists
        domain = re.sub(r'^www\.', '', domain)
        return domain
    except Exception:
        return None



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

def insert_activity(conn, timestamp, app_name, window_title, url, session_name, previous_time):
    """Insert a record of the activity into the database and update activity duration."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO activities (timestamp, app_name, window_title, url, session)
    VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, app_name, window_title, url, session_name))
    conn.commit()

    # Update the activity duration
    activity_key = extract_domain(url) if url else app_name
    if activity_key:
        activity_duration[activity_key] += (time.time() - previous_time)


def calculate_top_activities():
    """Calculate and return the top 5 activities by duration."""
    total_time = sum(activity_duration.values())
    if total_time == 0:
        return []
    
    sorted_activities = sorted(activity_duration.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_activities[:5]
    
    return [(activity, (duration / total_time) * 100) for activity, duration in top_5]


def display_top_activities(activities):
    """Display the top 5 activities with their percentages."""
    if activities:
        print("\nTop 5 Activities:")
        for activity, percentage in activities:
            print(f"{activity}: {percentage:.2f}%")
    else:
        print("No activities to display.")


@click.group()
def cli():
    """CLI application for tracking window activities."""
    pass

@cli.command()
def start():
    """Start tracking activities."""
    conn = sqlite3.connect('tracker.db')
    current_session = None
    session_start_time = None
    overall_start_time = time.time()
    previous_time = time.time()
    print("Activity tracking started.")
    print("Use 'n' to start a new session, 's' to stop the current session, or 'q' to quit.")

    try:
        while True:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            elapsed_time_overall = int(time.time() - overall_start_time)
            app_name, window_title, url = get_active_window_info()

            if app_name:
                insert_activity(conn, current_time, app_name, window_title, url, current_session, previous_time)
                previous_time = time.time()

            # Clear the console (for a cleaner interface)
            sys.stdout.write("\033c")
            sys.stdout.flush()

            # Display tracking status
            print(f"Tracking for {format_elapsed_time(elapsed_time_overall)}.")
            if current_session:
                elapsed_time_session = int(time.time() - session_start_time)
                session_start_str = time.strftime('%H:%M %d/%m/%Y', time.localtime(session_start_time))
                
                # Calculate days, hours, minutes, and seconds
                days, remainder = divmod(elapsed_time_session, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                # Build the elapsed time string
                elapsed_time_str = ""
                if days > 0:
                    elapsed_time_str += f"{days} days "
                if hours > 0:
                    elapsed_time_str += f"{hours} hours "
                if minutes > 0:
                    elapsed_time_str += f"{minutes} minutes "
                elapsed_time_str += f"{seconds} seconds"

                print(f"Current session: {current_session}")
                print(f"Session started at: {session_start_str} (Elapsed: {format_elapsed_time(elapsed_time_session)})")
                
                # Display top 5 activities for the session
                top_activities = calculate_top_activities()
                display_top_activities(top_activities)
            else:
                print("No active session.")
                
                # Display top 5 activities since tracking started
                top_activities = calculate_top_activities()
                display_top_activities(top_activities)

            # Input prompt (non-blocking)
            rlist, _, _ = select.select([sys.stdin], [], [], 0.9)
            if rlist:
                user_input = sys.stdin.readline().strip().lower()
                if user_input == 'n':
                    current_session = input("Enter new session name: ")
                    session_start_time = time.time()
                    previous_time = time.time()
                    print(f"New session started: {current_session}")
                    # Reset activity duration for the new session
                    activity_duration.clear()
                elif user_input == 's':
                    if current_session:
                        print(f"Session '{current_session}' stopped.")
                        current_session = None
                        session_start_time = None
                    else:
                        print("No active session to stop.")
                elif user_input == 'q':
                    break
                else:
                    print("Invalid command. Use 'n' for new session, 's' to stop session, or 'q' to quit.")

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

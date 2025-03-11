import select
import sys
import time
import click
from database_manager import DatabaseManager
from tracking.activity_tracker import ActivityTracker
from tracking.session_manager import SessionManager
from tracking.activity_analyzer import ActivityAnalyzer


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
    db_manager = DatabaseManager()
    db_manager.setup_database()

    # Initialize our components
    tracker = ActivityTracker(db_manager)
    session_manager = SessionManager(db_manager)
    analyzer = ActivityAnalyzer()

    print("Activity tracking started.")
    print(
        "Use 'n' to start a new session, 's' to stop the current session, or 'q' to quit."
    )

    previous_time = time.time()

    try:
        while True:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            session_info = session_manager.get_session_info()

            # Track the current activity
            app_name, window_title, url = tracker.track_activity(
                current_time, session_manager.current_session
            )

            # Update activity duration
            if app_name:
                duration = time.time() - previous_time
                analyzer.update_duration(app_name, window_title, url, duration)
                previous_time = time.time()

            # Clear the console (for a cleaner interface)
            sys.stdout.write("\033c")
            sys.stdout.flush()

            # Display tracking status
            print(f"Tracking for {session_info['formatted_elapsed_time_overall']}.")

            if session_manager.current_session:
                print(f"Current session: {session_manager.current_session}")
                print(
                    f"Session started at: {session_info['session_start_str']} (Elapsed: {session_info['formatted_elapsed_time_session']})"
                )

                # Display top 5 activities for the session
                top_activities = analyzer.calculate_top_activities()
                display_top_activities(top_activities)
            else:
                print("No active session.")

                # Display top 5 activities since tracking started
                top_activities = analyzer.calculate_top_activities()
                display_top_activities(top_activities)

            # Input prompt (non-blocking)
            rlist, _, _ = select.select([sys.stdin], [], [], 0.9)
            if rlist:
                user_input = sys.stdin.readline().strip().lower()
                if user_input == "n":
                    session_name = input("Enter new session name: ")
                    session_manager.start_session(session_name)
                    previous_time = time.time()
                    # Reset activity duration for the new session
                    analyzer.reset()
                elif user_input == "s":
                    session_manager.stop_session()
                elif user_input == "q":
                    break
                else:
                    print(
                        "Invalid command. Use 'n' for new session, 's' to stop session, or 'q' to quit."
                    )

            time.sleep(0.9)
    except KeyboardInterrupt:
        print("\nTracking stopped.")


@cli.command()
def stop():
    """Stop tracking activities."""
    # This command would be used to stop tracking
    # You might want to implement functionality to terminate the process or manage sessions.
    print("Stopping tracking is not yet implemented.")


if __name__ == "__main__":
    cli()

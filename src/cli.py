"""Command-line interface for the Intent-Aligned Focus Tracker."""

from datetime import datetime

from pydantic import BaseModel
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from src.coordinator import Coordinator
from src.logging import get_logger
from src.models import ActivitySnapshot, Session
from src.polling.mac_poller import MacOSPoller
from src.storage.sqlite_store import SQLiteStorage

logger = get_logger(__name__)
console = Console()


class TimelineBlock(BaseModel):
    """A contiguous block of time spent on the same activity.

    Attributes:
        label: Human-readable activity label (domain for browsers, app name otherwise).
        start: When this activity block began.
        end: When this activity block ended.
        duration_seconds: Total seconds spent on this activity.
    """
    label: str
    start: datetime
    end: datetime
    duration_seconds: float


def handle_exit(coordinator: Coordinator) -> None:
    """Handle exit logic: end active session if exists, then exit.

    Args:
        coordinator: The Coordinator instance managing sessions.
    """
    if coordinator.get_current_session() is not None:
        console.print("\n[yellow]Active session detected. Ending session...[/yellow]\n")
        handle_stop(coordinator)

    console.print("[yellow]Goodbye! 👋[/yellow]\n")


def main() -> None:
    """Main entry point for interactive CLI.

    Initializes storage and coordinator, then runs an interactive command loop
    for managing focus sessions.
    """
    console.print("\n[bold green]🔒 LockedIn - Focus Tracker[/bold green]")

    # Initialize storage (will fail if DB doesn't exist)
    try:
        storage = SQLiteStorage()
    except FileNotFoundError as e:
        console.print("\n[red]❌ Database not initialized![/red]")
        console.print("[yellow]Please run setup first:[/yellow]")
        console.print("[cyan]  uv run scripts/setup.py[/cyan]\n")
        return

    console.print("Starting background activity polling...\n")

    # Initialize coordinator (starts polling immediately)
    poller = MacOSPoller()
    coordinator = Coordinator(poller=poller, storage=storage)

    console.print("[dim]Type 'help' for available commands[/dim]\n")

    # Interactive command loop
    while True:
        try:
            command = Prompt.ask("[bold cyan]lockedin[/bold cyan]").strip().lower()

            if command == "exit" or command == "quit":
                handle_exit(coordinator)
                break

            elif command == "help":
                show_help()

            elif command == "start":
                handle_start(coordinator)

            elif command == "stop":
                handle_stop(coordinator)

            elif command == "status":
                handle_status(coordinator)

            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("[dim]Type 'help' for available commands[/dim]\n")

        except KeyboardInterrupt:
            # Handle Ctrl+C the same way as exit
            console.print("\n")
            handle_exit(coordinator)
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")
            logger.error(f"Command error: {e}")


def show_help() -> None:
    """Display help message with available commands.

    Shows a formatted table of all CLI commands and their descriptions.
    """
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")

    table.add_row("start", "Start a focus session")
    table.add_row("stop", "End current session and show summary")
    table.add_row("status", "Show current session status")
    table.add_row("help", "Show this help message")
    table.add_row("exit", "Quit LockedIn")

    console.print(table)
    console.print()


def handle_start(coordinator: Coordinator) -> None:
    """Handle the start command.

    Prompts user for task and goal, then starts a new focus session.

    Args:
        coordinator: The Coordinator instance managing sessions.
    """
    task = Prompt.ask("[bold]What are you working on?[/bold]")
    goal = Prompt.ask("[bold]What's the bigger goal?[/bold]")

    session = coordinator.start_session(task=task, goal=goal)

    console.print(f"\n[green]✓ Session started: {session.id}[/green]")
    console.print(f"[dim]Task: {session.task}[/dim]")
    console.print(f"[dim]Goal: {session.goal}[/dim]\n")


def handle_stop(coordinator: Coordinator) -> None:
    """Handle the stop command.

    Ends the current session, retrieves activities, and displays a timeline
    summary of the session.

    Args:
        coordinator: The Coordinator instance managing sessions.
    """
    try:
        session = coordinator.end_session()

        duration = (session.end_time - session.start_time).total_seconds()
        duration_mins = int(duration / 60)

        console.print(f"\n[green]✓ Session ended: {session.id}[/green]")
        console.print(f"[dim]Duration: {duration_mins} minutes[/dim]\n")

        # Get session activities and display timeline
        activities = coordinator.storage.get_session_activities(session.id)

        if not activities:
            console.print("[yellow]No activities recorded for this session[/yellow]\n")
            return

        # Build timeline by grouping consecutive same app/domain
        timeline = build_timeline(activities)

        # Display timeline
        display_timeline(timeline, session)

    except RuntimeError as e:
        console.print(f"[red]{e}[/red]\n")


def handle_status(coordinator: Coordinator) -> None:
    """Handle the status command.

    Displays current session information if in session mode, or idle mode
    status if no active session.

    Args:
        coordinator: The Coordinator instance managing sessions.
    """
    session = coordinator.get_current_session()

    if session is None:
        console.print("[yellow]Idle mode[/yellow] - No active session")
        console.print("[dim]Activities are being tracked but not tagged to a session[/dim]\n")
    else:
        duration = (datetime.now() - session.start_time).total_seconds()
        duration_mins = int(duration / 60)

        console.print(f"[green]Active session: {session.id}[/green]")
        console.print(f"Task: {session.task}")
        console.print(f"Goal: {session.goal}")
        console.print(f"Duration: {duration_mins} minutes\n")


def build_timeline(activities: list[ActivitySnapshot]) -> list[TimelineBlock]:
    """Group consecutive activities into timeline blocks.

    Consecutive activities with the same label (app/domain) are merged into
    a single timeline block. Blocks with duration less than 1 second are
    filtered out.

    Args:
        activities: List of ActivitySnapshot objects, sorted by timestamp.

    Returns:
        List of TimelineBlock objects with duration >= 1 second.
    """
    if not activities:
        return []

    timeline = []
    current_label = get_activity_label(activities[0])
    current_start = activities[0].timestamp
    current_end = activities[0].timestamp

    for activity in activities[1:]:
        label = get_activity_label(activity)

        if label == current_label:
            # Extend current block
            current_end = activity.timestamp
        else:
            # Save current block and start new one
            duration = (current_end - current_start).total_seconds()
            if duration >= 1.0:
                timeline.append(TimelineBlock(
                    label=current_label,
                    start=current_start,
                    end=current_end,
                    duration_seconds=duration
                ))

            current_label = label
            current_start = activity.timestamp
            current_end = activity.timestamp

    # Add final block if it meets duration threshold
    duration = (current_end - current_start).total_seconds()
    if duration >= 1.0:
        timeline.append(TimelineBlock(
            label=current_label,
            start=current_start,
            end=current_end,
            duration_seconds=duration
        ))

    return timeline


def get_activity_label(activity: ActivitySnapshot) -> str:
    """Get display label for an activity.

    For browsers, uses domain. For other apps, uses app name.

    Args:
        activity: ActivitySnapshot object.

    Returns:
        Human-readable label (domain or app name).
    """
    if activity.domain:
        return activity.domain
    return activity.app_name


def display_timeline(timeline: list[TimelineBlock], session: Session) -> None:
    """Display the session timeline as a Rich table.

    Creates a formatted table showing start time, end time, duration, and
    activity label for each timeline block.

    Args:
        timeline: List of TimelineBlock objects to display.
        session: The Session object for context (used in table title).
    """
    table = Table(title=f"Session Timeline: {session.task}")
    table.add_column("Start", style="cyan")
    table.add_column("End", style="cyan")
    table.add_column("Duration", style="yellow", justify="right")
    table.add_column("Activity", style="white")

    for block in timeline:
        start_str = block.start.strftime("%H:%M:%S")
        end_str = block.end.strftime("%H:%M:%S")

        # Format duration
        duration_secs = int(block.duration_seconds)
        if duration_secs < 60:
            duration_str = f"{duration_secs}s"
        else:
            mins = duration_secs // 60
            secs = duration_secs % 60
            duration_str = f"{mins}m {secs}s"

        table.add_row(
            start_str,
            end_str,
            duration_str,
            block.label
        )

    console.print(table)
    console.print()


if __name__ == "__main__":
    main()

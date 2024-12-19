import click
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

MAX_GAP = 10  # Maximum gap in seconds (10 seconds) before considering it as inactivity
MAX_ACTIVITY_LENGTH = 50  # Maximum length for activity names before truncation

console = Console()

def get_db_connection():
    return sqlite3.connect('tracker.db')

def get_domain(url):
    try:
        return urlparse(url).netloc
    except Exception:
        return "Unknown"

def truncate_string(s, max_length):
    return s[:max_length-3] + '...' if len(s) > max_length else s

def process_activities(results):
    activity_summary = defaultdict(int)
    total_duration = 0
    last_timestamp = None
    last_activity = None
    gaps = []

    for row in results:
        timestamp, app_name, window_title, url = row[1:5]
        current_timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        activity = url if app_name in ['Brave Browser', 'Google Chrome', 'Safari', 'Firefox'] else app_name
        if activity.startswith('http'):
            activity = get_domain(activity)

        if last_timestamp and last_activity:
            duration = (current_timestamp - last_timestamp).total_seconds()
            if duration > MAX_GAP or last_activity == "loginwindow":
                gaps.append((last_timestamp, current_timestamp, duration))
            elif last_activity != "loginwindow":
                activity_summary[last_activity] += duration
                total_duration += duration

        last_timestamp = current_timestamp
        last_activity = activity

    return activity_summary, total_duration, gaps

def format_time(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

@click.group()
def cli():
    """Personal Activity Tracker CLI"""
    pass

@cli.command()
@click.option('--hours', type=int, help='Number of hours to summarize')
@click.option('--minutes', type=int, help='Number of minutes to summarize')
def summary(hours, minutes):
    """Provide a summary of activities for the last specified time period"""
    if hours is None and minutes is None:
        console.print("[bold red]Please specify either --hours or --minutes[/bold red]")
        return
    if hours is not None and minutes is not None:
        console.print("[bold red]Please specify either --hours or --minutes, not both[/bold red]")
        return

    if hours is not None:
        time_delta = timedelta(hours=hours)
        time_unit = "hour(s)"
        time_value = hours
    else:
        time_delta = timedelta(minutes=minutes)
        time_unit = "minute(s)"
        time_value = minutes

    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now()
    start_time = now - time_delta

    query = '''
    SELECT *
    FROM activities
    WHERE timestamp >= ? AND timestamp < ?
    ORDER BY timestamp
    '''

    cursor.execute(query, (start_time.strftime("%Y-%m-%d %H:%M:%S"),
                           now.strftime("%Y-%m-%d %H:%M:%S")))
    results = cursor.fetchall()

    activity_summary, total_duration, gaps = process_activities(results)

    console.print(Panel(f"[bold cyan]Activity Summary for the last {time_value} {time_unit}[/bold cyan]",
                        expand=False, border_style="cyan"))

    if results:
        console.print(f"[green]Data range:[/green] {results[0][1]} to {results[-1][1]}")

    requested_duration = time_delta.total_seconds()
    total_gap_time = requested_duration - total_duration

    table = Table(title="Time Summary", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Duration", style="magenta")
    table.add_row("Total tracked time", format_time(total_duration))
    table.add_row("Requested duration", str(time_delta))
    table.add_row("Total gap time", format_time(total_gap_time))
    console.print(table)

    coverage_percentage = (total_duration / requested_duration) * 100
    console.print(f"[bold green]Tracking coverage:[/bold green] {coverage_percentage:.2f}%")

    if gaps:
        console.print(f"\n[yellow]Detected gaps within tracked time:[/yellow] {len(gaps)}")
        console.print("[yellow]Largest gaps within tracked time:[/yellow]")
        for start, end, duration in sorted(gaps, key=lambda x: x[2], reverse=True)[:5]:
            console.print(f"  From {start} to {end} ({format_time(duration)})")

    console.print("\n[bold cyan]Top activities (% of tracked time, excluding sleep):[/bold cyan]")
    activities_table = Table(box=box.SIMPLE)
    activities_table.add_column("Activity", style="cyan")
    activities_table.add_column("Duration", style="magenta")
    activities_table.add_column("Percentage", style="green")

    for activity, duration in sorted(activity_summary.items(), key=lambda x: x[1], reverse=True):
        if activity != "loginwindow":
            percentage = (duration / total_duration) * 100
            if percentage > 0.5:
                activities_table.add_row(
                    truncate_string(activity, MAX_ACTIVITY_LENGTH),
                    format_time(duration),
                    f"{percentage:.2f}%"
                )

    console.print(activities_table)

    # Add a note about sleep time
    sleep_time = sum(duration for start, end, duration in gaps if duration > MAX_GAP)
    console.print(f"\n[yellow]Note: Your device was likely asleep or locked for approximately {format_time(sleep_time)}.[/yellow]")

    conn.close()

@cli.command()
@click.option('--hours', type=int, help='Number of hours to show timeline for')
@click.option('--minutes', type=int, help='Number of minutes to show timeline for')
def timeline(hours, minutes):
    """Show a timeline of activities for the specified period"""
    if hours is None and minutes is None:
        console.print("[bold red]Please specify either --hours or --minutes[/bold red]")
        return
    if hours is not None and minutes is not None:
        console.print("[bold red]Please specify either --hours or --minutes, not both[/bold red]")
        return

    if hours is not None:
        time_delta = timedelta(hours=hours)
        time_unit = "hour(s)"
        time_value = hours
    else:
        time_delta = timedelta(minutes=minutes)
        time_unit = "minute(s)"
        time_value = minutes

    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now()
    start_time = now - time_delta

    query = '''
    SELECT *
    FROM activities
    WHERE timestamp >= ? AND timestamp < ?
    ORDER BY timestamp
    '''

    cursor.execute(query, (start_time.strftime("%Y-%m-%d %H:%M:%S"),
                          now.strftime("%Y-%m-%d %H:%M:%S")))
    results = cursor.fetchall()

    if not results:
        console.print("[yellow]No activities found in this time period[/yellow]")
        return

    console.print(Panel(f"[bold cyan]Activity Timeline for the last {time_value} {time_unit}[/bold cyan]",
                       expand=False, border_style="cyan"))

    current_activity = None
    activity_start = None

    table = Table(box=box.SIMPLE)
    table.add_column("Time Range", style="cyan")
    table.add_column("Activity", style="magenta")
    table.add_column("Duration", style="green")

    for i, row in enumerate(results):
        timestamp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        app_name = row[2]
        url = row[4]

        activity = url if app_name in ['Brave Browser', 'Google Chrome', 'Safari', 'Firefox'] else app_name
        if activity.startswith('http'):
            activity = get_domain(activity)

        if current_activity is None:
            current_activity = activity
            activity_start = timestamp
        elif activity != current_activity or i == len(results) - 1:
            # Add the completed activity period to the table
            duration = (timestamp - activity_start).total_seconds()
            if duration > MAX_GAP and current_activity != "loginwindow":
                time_range = f"{activity_start.strftime('%I:%M %p')} - {timestamp.strftime('%I:%M %p')}"
                table.add_row(
                    time_range,
                    truncate_string(current_activity, MAX_ACTIVITY_LENGTH),
                    format_time(duration)
                )

            current_activity = activity
            activity_start = timestamp

    console.print(table)
    conn.close()

if __name__ == '__main__':
    cli()

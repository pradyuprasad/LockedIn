import click
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

MAX_GAP = 300  # Maximum gap in seconds (5 minutes) before considering it as inactivity

console = Console()

def get_db_connection():
    return sqlite3.connect('tracker.db')

def get_domain(url):
    try:
        return urlparse(url).netloc
    except:
        return "Unknown"

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
            if duration > MAX_GAP:
                gaps.append((last_timestamp, current_timestamp, duration))
            else:
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
    
    console.print("\n[bold cyan]Top activities (% of tracked time):[/bold cyan]")
    activities_table = Table(box=box.SIMPLE)
    activities_table.add_column("Activity", style="cyan")
    activities_table.add_column("Duration", style="magenta")
    activities_table.add_column("Percentage", style="green")

    for activity, duration in sorted(activity_summary.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (duration / total_duration) * 100
        activities_table.add_row(
            activity, 
            format_time(duration),
            f"{percentage:.2f}%"
        )

    console.print(activities_table)

    conn.close()

if __name__ == '__main__':
    cli()
import os
import time
from datetime import datetime
from activity_viz import process_activities, format_time, truncate_string
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from database_manager import DatabaseManager

console = Console()
REFRESH_INTERVAL = 10  # Refresh every 10 seconds

def get_db_connection():
    db_manager = DatabaseManager()
    return db_manager.get_connection()

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def visualize_today():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Define the time range (since midnight today)
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    query = '''
    SELECT *
    FROM activities
    WHERE timestamp >= ? AND app_name != 'loginwindow'
    ORDER BY timestamp
    '''

    # Execute query
    cursor.execute(query, (start_of_day.strftime("%Y-%m-%d %H:%M:%S"),))
    results = cursor.fetchall()

    # Process activities
    activity_summary, total_duration, gaps = process_activities(results)

    # Display the summary panel
    console.print(Panel("[bold cyan]Activity Summary Since Midnight[/bold cyan]",
                        expand=False, border_style="cyan"))

    # Create the summary table
    table = Table(title="Today's Activities", box=box.ROUNDED)
    table.add_column("Activity", style="cyan", justify="left")
    table.add_column("Duration", style="magenta", justify="right")
    table.add_column("Percentage", style="green", justify="right")

    for activity, duration in sorted(activity_summary.items(), key=lambda x: x[1], reverse=True):
        percentage = (duration / total_duration) * 100
        table.add_row(truncate_string(activity, 50), format_time(duration), f"{percentage:.2f}%")

    console.print(table)

    # Display additional stats
    console.print(f"[green]Total Tracked Time:[/green] {format_time(total_duration)}")
    if gaps:
        total_gap_time = sum(duration for _, _, duration in gaps)
        console.print(f"[yellow]Total Gap Time (Inactivity):[/yellow] {format_time(total_gap_time)}")
        console.print(f"[yellow]Number of Gaps Detected:[/yellow] {len(gaps)}")

    conn.close()

if __name__ == "__main__":
    try:
        while True:
            clear_screen()
            console.print(f"Updates every {REFRESH_INTERVAL} seconds...\n", style="bold yellow")
            visualize_today()
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        console.print("\n[bold red]Visualization stopped by user.[/bold red]")

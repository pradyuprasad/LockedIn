import click
import sqlite3
from collections import defaultdict
import plotext as plt
from datetime import datetime, timedelta
from urllib.parse import urlparse

def get_db_connection():
    return sqlite3.connect('tracker.db')

def get_domain(url):
    try:
        return urlparse(url).netloc
    except:
        return "Unknown"

@click.group()
def cli():
    """Personal Activity Tracker CLI"""
    pass

@cli.command()
@click.option('--days', type=int, help='Number of days to summarize')
@click.option('--hours', type=int, help='Number of hours to summarize')
def summary(days, hours):
    """Provide a summary of activities"""
    if not days and not hours:
        click.echo("Please specify either --days or --hours")
        return
    if days and hours:
        click.echo("Please specify either --days or --hours, not both")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if days:
        time_clause = f"timestamp >= datetime('now', '-{days} days')"
        period_str = f"{days} days"
    else:
        time_clause = f"timestamp >= datetime('now', '-{hours} hours')"
        period_str = f"{hours} hours"
    
    query = f'''
    SELECT 
        timestamp,
        CASE 
            WHEN app_name IN ('Brave Browser', 'Google Chrome', 'Safari', 'Firefox') THEN 
                url
            ELSE app_name 
        END as activity
    FROM activities
    WHERE {time_clause}
    ORDER BY timestamp
    '''
    cursor.execute(query)
    results = cursor.fetchall()

    time_summary = defaultdict(lambda: defaultdict(int))
    for i in range(len(results) - 1):
        current_time, activity = results[i]
        next_time, _ = results[i + 1]
        if activity.startswith('http'):
            activity = get_domain(activity)
        
        current_dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        next_dt = datetime.strptime(next_time, "%Y-%m-%d %H:%M:%S")
        duration = (next_dt - current_dt).total_seconds()
        
        time_key = current_time.split()[0] if days else current_time.split()[1].split(':')[0]  # Date or Hour
        time_summary[time_key][activity] += duration

    print(f"\nActivity Summary for the last {period_str}")
    print("=" * 40)

    for time_key, activities in time_summary.items():
        print(f"\n{'Date' if days else 'Hour'}: {time_key}")
        total_seconds = sum(activities.values())
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, _ = divmod(remainder, 60)
        print(f"Total time: {hours}h {minutes}m")
        print("Top activities:")
        for activity, seconds in sorted(activities.items(), key=lambda x: x[1], reverse=True)[:5]:
            activity_hours, activity_remainder = divmod(int(seconds), 3600)
            activity_minutes, _ = divmod(activity_remainder, 60)
            print(f"  {activity}: {activity_hours}h {activity_minutes}m")

    conn.close()

if __name__ == '__main__':
    cli()
import time
import click
from datetime import datetime
from pathlib import Path
import sqlite3
import yaml
from typing import Dict, Optional

from focus_utils import (
    notify, calculate_activity_metrics, calculate_score_components,
    get_score_emoji
)

class FocusSession:
    def __init__(self, config_path='focus_config.yml'):
        self.load_config(config_path)
        self.db_conn = sqlite3.connect('tracker.db')
        self.session_start = None
        self.last_violation_time = None
        self.violations = []
        self.current_violation = None
        self.violation_start_time = None
        self.MIN_VIOLATION_TIME = 30

        # You can update or add new keys in score_config if desired
        self.score_config = {
            'DEEP_WORK_THRESHOLD': 1800,    # 30 minutes
            'SHALLOW_THRESHOLD': 300,       # 5 minutes
            'MICRO_SWITCH_THRESHOLD': 60,   # 1 minute
            'RAPID_SWITCH_PENALTY': -15,
            'MICRO_SWITCH_PENALTY': -5,
            'SHALLOW_SWITCH_PENALTY': -3,
            'DEEP_WORK_BONUS': 10,
            'SHALLOW_WORK_PENALTY': -30,
            'FRAGMENTATION_PENALTY': -40,
            'target_duration_minutes': 60,

            # New optional keys for refined logic in focus_utils
            'SHORT_SWITCH_DEV_PENALTY_UNDER_10': -5,
            'SHORT_SWITCH_NON_DEV_PENALTY_UNDER_10': -15,
            'SHORT_SWITCH_DEV_PENALTY_UNDER_30': 0,
            'SHORT_SWITCH_NON_DEV_PENALTY_UNDER_30': -10,
            'CLUSTER_SWITCH_PENALTY': -2,
            'FOCUS_PERIOD_REWARD': 10,
            'DEEP_FOCUS_REWARD': 15,
            'EXTENDED_FOCUS_REWARD': 20
        }

    def load_config(self, config_path: str) -> None:
        if not Path(config_path).exists():
            default_config = {
                'whitelist': {
                    'apps': ['Visual Studio Code', 'PyCharm', 'Terminal'],
                    'domains': ['github.com', 'stackoverflow.com', 'docs.python.org']
                },
                'blacklist': {
                    'apps': ['Messages', 'Mail'],
                    'domains': ['twitter.com', 'facebook.com', 'youtube.com']
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f)

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def is_violation(self, app_name: str, url: Optional[str]) -> Optional[str]:
        if app_name in self.config['blacklist']['apps']:
            return app_name

        if url:
            for domain in self.config['blacklist']['domains']:
                if domain in url:
                    return domain

        return None

    def get_score_breakdown(self) -> Dict:
        if not self.session_start:
            return {"score": 0, "components": [], "timeline": []}

        cursor = self.db_conn.cursor()
        session_start_str = self.session_start.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            SELECT timestamp, app_name, url
            FROM activities
            WHERE timestamp >= ?
            ORDER BY timestamp
        ''', (session_start_str,))

        activities = cursor.fetchall()
        metrics = calculate_activity_metrics(activities, self.score_config)
        components, final_score = calculate_score_components(metrics, self.score_config)

        return {
            "score": final_score,
            "components": components,
            "timeline": metrics['timeline']
        }

    def format_time_remaining(self) -> str:
        if not self.session_start:
            return "0:00"

        elapsed_seconds = (datetime.now() - self.session_start).total_seconds()
        remaining_seconds = max(0, self.score_config['target_duration_minutes'] * 60 - elapsed_seconds)

        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def check_current_activity(self) -> None:
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT timestamp, app_name, url
            FROM activities
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        if not row:
            return

        timestamp, app_name, url = row
        violation = self.is_violation(app_name, url)

        current_time = datetime.now()

        if violation:
            if not self.violation_start_time:
                self.violation_start_time = current_time
                self.current_violation = violation
            elif violation != self.current_violation:
                self.violation_start_time = current_time
                self.current_violation = violation
            elif (current_time - self.violation_start_time).total_seconds() >= self.MIN_VIOLATION_TIME:
                if not self.last_violation_time or \
                   (current_time - self.last_violation_time).total_seconds() > 60:
                    self.violations.append({
                        'time': current_time,
                        'app_or_site': violation,
                        'duration': (current_time - self.violation_start_time).total_seconds()
                    })
                    notify(
                        "Focus Mode Warning",
                        f"Spent over {self.MIN_VIOLATION_TIME}s on {violation}"
                    )
                    self.last_violation_time = current_time
        else:
            self.violation_start_time = None
            self.current_violation = None

    def display_session_status(self) -> None:
        current_time = datetime.now()
        duration = current_time - self.session_start
        print("\nDeep Work Session Status:")
        print(f"Duration: {duration.seconds // 3600}h {(duration.seconds // 60) % 60}m {duration.seconds % 60}s")
        print(f"Time Remaining: {self.format_time_remaining()}")
        print(f"Context Switches: {len(self.violations)}")

    def display_score_info(self) -> None:
        score_data = self.get_score_breakdown()
        current_score = score_data["score"]
        score_emoji = get_score_emoji(current_score)
        # Simple color logic for demonstration
        score_color = "\033[92m" if current_score >= 70 else "\033[93m" if current_score >= 0 else "\033[91m"

        print(f"\nDeep Work Score: {score_color}{current_score:.1f} {score_emoji}\033[0m")
        print("\nScore Breakdown:")
        for component, value, explanation in score_data["components"]:
            if value is not None:
                sign = "+" if value > 0 else ""
                color = "\033[92m" if value > 0 else "\033[91m" if value < 0 else "\033[0m"
                print(f"  {color}{component}: {sign}{value:.1f}\033[0m")
                if explanation:
                    print(f"    → {explanation}")

    def display_violations(self) -> None:
        current_time = datetime.now()
        if self.current_violation:
            violation_duration = (current_time - self.violation_start_time).seconds
            print(f"\n⚠️  Current distraction: {self.current_violation} ({violation_duration}s)")

        if self.violations:
            print("\nRecent distractions:")
            recent_violations = self.violations[-3:]
            for v in reversed(recent_violations):
                print(f"- {v['app_or_site']} at {v['time'].strftime('%H:%M:%S')}")

    def start(self) -> None:
        self.session_start = datetime.now()
        notify("Focus Mode", "Focus session started")
        print(f"\nFocus session started at {self.session_start.strftime('%H:%M:%S')}")
        print("Monitoring for distractions...")
        print("Press Ctrl+C to end session")

        try:
            while True:
                print("\033c", end="")
                self.display_session_status()
                self.display_score_info()
                self.display_violations()
                self.check_current_activity()
                time.sleep(2)

        except KeyboardInterrupt:
            self.end()

    def end(self) -> None:
        if not self.session_start:
            return

        duration = datetime.now() - self.session_start
        final_score = self.calculate_current_score()

        print("\nDeep Work Session Summary:")
        print(f"Duration: {duration.seconds // 3600}h {(duration.seconds // 60) % 60}m {duration.seconds % 60}s")
        print(f"Context Switches: {len(self.violations)}")
        print(f"Final Deep Work Score: {final_score:.1f}/100 {get_score_emoji(final_score)}")

        if self.violations:
            print("\nDistraction breakdown:")
            violation_counts = {}
            for v in self.violations:
                violation_counts[v['app_or_site']] = violation_counts.get(v['app_or_site'], 0) + 1

            for app_or_site, count in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"- {app_or_site}: {count} times")

        notify(
            "Deep Work Session Ended",
            f"Duration: {duration}\nSwitches: {len(self.violations)}\nScore: {final_score:.1f}/100"
        )

    def calculate_current_score(self) -> float:
        """Simple helper to get final score as float. Adjust as needed."""
        score_data = self.get_score_breakdown()
        return score_data["score"]

def test_notification():
    """Test if notifications are working"""
    try:
        notify("Test Notification", "If you see this, notifications are working!")
        return True
    except Exception as e:
        print(f"Notification failed: {e}")
        print("Please check if notifications are enabled for your terminal/Python")
        return False

@click.group()
def cli():
    """Focus mode commands"""
    pass

@cli.command()
def start():
    """Start a focus session"""
    session = FocusSession()
    print("Testing notifications...")
    test_notification()
    time.sleep(2)
    session.start()

if __name__ == '__main__':
    cli()

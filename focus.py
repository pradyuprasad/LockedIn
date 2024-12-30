import sqlite3
import time
import yaml
import subprocess
from datetime import datetime
import click
from pathlib import Path

def notify(title, message):
    """Multi-channel notification"""
    try:
        # 1. System notification
        subprocess.run([
            'osascript',
            '-e', f'display notification "{message}" with title "{title}" sound name "Glass"'
        ])

        # 2. Terminal bell (makes a sound and may flash the terminal)
        print('\a', flush=True)

        # 3. Print to terminal with visible formatting
        print(f"\n🚨 {title}: {message}")

    except Exception as e:
        print(f"Error sending notification: {e}")

class FocusSession:
    def __init__(self, config_path='focus_config.yml'):
        self.load_config(config_path)
        self.db_conn = sqlite3.connect('tracker.db')
        self.session_start = None
        self.last_violation_time = None
        self.violations = []
        self.current_violation = None
        self.violation_start_time = None
        self.MIN_VIOLATION_TIME = 5  # seconds before counting as violation

        # Score configuration
        self.score_config = {
            'base_score': 100,
            'duration_bonus_cap': 20,
            'violation_penalty': 5,
            'current_violation_penalty': 10,
            'target_duration_minutes': 60
        }

    def load_config(self, config_path):
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

    def is_violation(self, app_name, url):
        if app_name in self.config['blacklist']['apps']:
            return app_name

        if url:
            for domain in self.config['blacklist']['domains']:
                if domain in url:
                    return domain

        return None

    def calculate_current_score(self):
        """Calculate the current focus score based on session duration and violations"""
        if not self.session_start:
            return 0

        current_time = datetime.now()
        duration_minutes = (current_time - self.session_start).total_seconds() / 60

        # Base score starts at 100
        base_score = self.score_config['base_score']

        # Duration bonus: up to 20 points for longer sessions
        duration_bonus = min(self.score_config['duration_bonus_cap'],
                           duration_minutes / 30)

        # Violation penalty: -5 points per violation
        violation_penalty = len(self.violations) * self.score_config['violation_penalty']

        # Current violation penalty: -10 points if currently in violation
        current_violation_penalty = (self.score_config['current_violation_penalty']
                                   if self.violation_start_time else 0)

        # Calculate final score
        score = max(0, base_score + duration_bonus - violation_penalty - current_violation_penalty)

        return score

    def get_score_emoji(self, score):
        """Return an appropriate emoji based on the focus score"""
        if score >= 90:
            return "🌟"
        elif score >= 80:
            return "✨"
        elif score >= 70:
            return "😊"
        elif score >= 60:
            return "😐"
        else:
            return "😟"

    def format_time_remaining(self, target_duration_minutes=25):
        """Format remaining time for a target session duration"""
        if not self.session_start:
            return "0:00"

        elapsed_seconds = (datetime.now() - self.session_start).total_seconds()
        remaining_seconds = max(0, target_duration_minutes * 60 - elapsed_seconds)

        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def check_current_activity(self):
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
                # Reset timer if switched to different violation
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

    def start(self):
        self.session_start = datetime.now()
        notify("Focus Mode", "Focus session started")

        print(f"\nFocus session started at {self.session_start.strftime('%H:%M:%S')}")
        print("Monitoring for distractions...")
        print("Press Ctrl+C to end session")

        try:
            while True:
                # Clear the screen
                print("\033c", end="")

                # Display current session info
                current_time = datetime.now()
                duration = current_time - self.session_start

                print("\nFocus Session Status:")
                print(f"Duration: {duration.seconds // 3600}h {(duration.seconds // 60) % 60}m {duration.seconds % 60}s")
                print(f"Time Remaining: {self.format_time_remaining(self.score_config['target_duration_minutes'])}")
                print(f"Distractions: {len(self.violations)}")

                # Display current focus score
                current_score = self.calculate_current_score()
                score_emoji = self.get_score_emoji(current_score)
                score_color = "\033[92m" if current_score >= 80 else "\033[93m" if current_score >= 60 else "\033[91m"
                print(f"\nCurrent Focus Score: {score_color}{current_score:.1f}/100 {score_emoji}\033[0m")

                # Display current violation if any
                if self.current_violation:
                    violation_duration = (current_time - self.violation_start_time).seconds
                    print(f"\n⚠️  Current distraction: {self.current_violation} ({violation_duration}s)")

                # Display recent violations
                if self.violations:
                    print("\nRecent distractions:")
                    recent_violations = self.violations[-3:]  # Show last 3 violations
                    for v in reversed(recent_violations):
                        print(f"- {v['app_or_site']} at {v['time'].strftime('%H:%M:%S')}")

                self.check_current_activity()
                time.sleep(2)  # Update every 2 seconds

        except KeyboardInterrupt:
            self.end()

    def end(self):
        if not self.session_start:
            return

        duration = datetime.now() - self.session_start
        final_score = self.calculate_current_score()

        print("\nFocus Session Summary:")
        print(f"Duration: {duration.seconds // 3600}h {(duration.seconds // 60) % 60}m {duration.seconds % 60}s")
        print(f"Number of distractions: {len(self.violations)}")
        print(f"Final Focus Score: {final_score:.1f}/100 {self.get_score_emoji(final_score)}")

        if self.violations:
            print("\nDistraction breakdown:")
            violation_counts = {}
            for v in self.violations:
                violation_counts[v['app_or_site']] = violation_counts.get(v['app_or_site'], 0) + 1

            for app_or_site, count in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"- {app_or_site}: {count} times")

        notify(
            "Focus Session Ended",
            f"Duration: {duration}\nDistractions: {len(self.violations)}\nScore: {final_score:.1f}/100"
        )

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

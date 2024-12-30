import sqlite3
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse

def notify(title: str, message: str) -> None:
    """Multi-channel notification"""
    try:
        # System notification
        subprocess.run([
            'osascript',
            '-e', f'display notification "{message}" with title "{title}" sound name "Glass"'
        ])

        # Terminal bell
        print('\a', flush=True)

        # Terminal print
        print(f"\n🚨 {title}: {message}")

    except Exception as e:
        print(f"Error sending notification: {e}")

def get_activity_identifier(app_name: str, url: Optional[str]) -> str:
    """Extract identifier from app or URL"""
    if url:
        try:
            return urlparse(url).netloc
        except Exception:
            return url
    return app_name

def calculate_activity_metrics(activities: List[Tuple[str, str, str]],
                             score_config: Dict[str, int]) -> Dict[str, Any]:
    """Analyze activity patterns and calculate metrics"""
    metrics = {
        'shallow_work_count': 0,
        'deep_work_count': 0,
        'micro_switches': 0,
        'rapid_switch_streak': 0,
        'total_switches': 0,
        'switches_under_60': 0,
        'timeline': [],
        'durations': []  # Add this key to store activity durations
    }

    prev_activity = None
    prev_time = None

    for timestamp, app_name, url in activities:
        current_activity = get_activity_identifier(app_name, url)
        current_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        if prev_activity and prev_time:
            duration = (current_time - prev_time).total_seconds()

            # Store duration in the metrics
            metrics['durations'].append(duration)

            if current_activity != prev_activity:
                metrics['total_switches'] += 1

                metrics['timeline'].append({
                    'time': current_time,
                    'from': prev_activity,
                    'to': current_activity,
                    'duration': duration
                })

                if duration <= score_config['MICRO_SWITCH_THRESHOLD']:
                    metrics['micro_switches'] += 1
                    metrics['rapid_switch_streak'] += 1
                    metrics['switches_under_60'] += 1
                else:
                    metrics['rapid_switch_streak'] = 0

                if duration <= score_config['SHALLOW_THRESHOLD']:
                    metrics['shallow_work_count'] += 1
                elif duration >= score_config['DEEP_WORK_THRESHOLD']:
                    metrics['deep_work_count'] += 1

        prev_activity = current_activity
        prev_time = current_time

    return metrics
def calculate_score_components(metrics: Dict[str, Any],
                             score_config: Dict[str, int]) -> List[Tuple[str, float, str]]:
    """Calculate score components based on metrics"""
    components = [("Base score", 100, None)]
    score = 100

    # Define task clusters
    dev_tools = {'Code', 'Terminal', 'localhost:3080', 'claude.ai'}

    # Process each activity/switch
    task_switches = 0
    for entry in metrics['timeline']:
        duration = entry['duration']
        from_tool = entry['from']
        to_tool = entry['to']

        # Penalize short switches regardless of tool type
        if duration < 30:
            score -= 15
            components.append((
                "Short Switch",
                -15,
                f"Switch under 30s: {from_tool} → {to_tool}"
            ))

        # Count task switches (between different clusters)
        if not (from_tool in dev_tools and to_tool in dev_tools):
            task_switches += 1

    # Penalize task switches between clusters
    if task_switches > 0:
        switch_penalty = task_switches * -2
        components.append((
            "Task Switches",
            switch_penalty,
            f"{task_switches} switches between different tasks"
        ))
        score += switch_penalty

    # Reward sustained focus periods
    for duration in metrics['durations']:
        if duration > 180:    # 3+ minutes
            score += 10
            components.append((
                "Focus Period",
                10,
                "Sustained focus over 3m"
            ))
        if duration > 300:    # 5+ minutes
            score += 15
            components.append((
                "Deep Focus",
                15,
                "Sustained focus over 5m"
            ))
        if duration > 600:    # 10+ minutes
            score += 20
            components.append((
                "Extended Focus",
                20,
                "Sustained focus over 10m"
            ))

    # No max/min limits on score
    return components, score
def get_score_emoji(score: float) -> str:
    """Return an appropriate emoji based on the focus score"""
    if score >= 90:
        return "🌟"
    elif score >= 80:
        return "✨"
    elif score >= 70:
        return "😊"
    elif score >= 60:
        return "😐"
    elif score >= 0:
        return "😟"
    else:
        return "💀"

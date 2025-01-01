import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse

def notify(title: str, message: str) -> None:
    """Multi-channel notification"""
    try:
        # System notification (macOS example via AppleScript)
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
    """Extract identifier from app or URL."""
    if url:
        try:
            # Grab the netloc (domain) from the URL
            return urlparse(url).netloc
        except Exception:
            return url
    return app_name

def calculate_activity_metrics(
    activities: List[Tuple[str, str, str]],
    score_config: Dict[str, int]
) -> Dict[str, Any]:
    """
    Analyze activity patterns and calculate metrics.
    Returns a metrics dict with:
       'shallow_work_count', 'deep_work_count', 'micro_switches', 'rapid_switch_streak',
       'total_switches', 'switches_under_60', 'timeline', 'durations'.
    """

    metrics = {
        'shallow_work_count': 0,
        'deep_work_count': 0,
        'micro_switches': 0,
        'rapid_switch_streak': 0,
        'total_switches': 0,
        'switches_under_60': 0,
        'timeline': [],
        'durations': []
    }

    MERGE_GAP = 30  # Maximum gap to merge consecutive identical activities (in seconds)
    merged_activities = []

    current_activity = None
    activity_start = None
    prev_time = None

    def add_activity(start, end, activity):
        if start and end and activity:
            duration = (end - start).total_seconds()
            merged_activities.append((start, end, duration, activity))
            metrics['durations'].append(duration)

    for timestamp, app_name, url in activities:
        if app_name == "loginwindow":
            continue
        # Convert DB string timestamp to datetime
        current_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        activity = get_activity_identifier(app_name, url)

        # Detect a switch
        if activity != current_activity:
            # If there's a significant gap since last timestamp, treat it as a separate block
            if prev_time and (current_time - prev_time).total_seconds() > MERGE_GAP:
                add_activity(activity_start, prev_time, current_activity)
                activity_start = current_time
            elif not activity_start:
                # First activity encountered
                activity_start = current_time
            else:
                # Switch within MERGE_GAP
                add_activity(activity_start, prev_time, current_activity)
                activity_start = current_time

                # Record a switch in the timeline
                metrics['total_switches'] += 1
                switch_duration = (current_time - prev_time).total_seconds()

                metrics['timeline'].append({
                    'time': current_time,
                    'from': current_activity,
                    'to': activity,
                    'duration': switch_duration
                })

                if switch_duration <= score_config.get('MICRO_SWITCH_THRESHOLD', 60):
                    metrics['micro_switches'] += 1
                    metrics['rapid_switch_streak'] += 1
                    metrics['switches_under_60'] += 1
                else:
                    metrics['rapid_switch_streak'] = 0

            current_activity = activity
        prev_time = current_time

    # Handle the last activity block
    if activity_start and prev_time and current_activity:
        add_activity(activity_start, prev_time, current_activity)

    return metrics

def calculate_score_components(
    metrics: Dict[str, Any],
    score_config: Dict[str, int]
) -> Tuple[List[Tuple[str, float, str]], float]:
    """
    Calculate score components based on metrics.
    Returns (components, total_score).
    """

    # *** Define your dev cluster or "safe" cluster here ***
    dev_tools = {
        'Code',
        'Terminal',
        'localhost:3080',
        'claude.ai',
        'chatgpt.com'
        'arxiv.org',
        'Obsidian'
    }

    components = []
    total_score = 0
    task_switches = 0

    for entry in metrics['timeline']:
        duration = entry['duration']
        from_tool = entry['from']
        to_tool = entry['to']

        # Determine cluster membership
        from_dev = from_tool in dev_tools
        to_dev = to_tool in dev_tools
        switch_is_dev_cluster = from_dev and to_dev

        # Check short switch durations
        if duration < 30:
            if duration < 10:
                if switch_is_dev_cluster:
                    penalty = score_config.get('SHORT_SWITCH_DEV_PENALTY_UNDER_10', -5)
                    reason = f"Short switch (<10s) in dev cluster: {from_tool} → {to_tool}"
                else:
                    penalty = score_config.get('SHORT_SWITCH_NON_DEV_PENALTY_UNDER_10', -15)
                    reason = f"Short switch (<10s) outside dev cluster: {from_tool} → {to_tool}"
            else:
                # 10s <= duration < 30s
                if switch_is_dev_cluster:
                    penalty = score_config.get('SHORT_SWITCH_DEV_PENALTY_UNDER_30', 0)
                    reason = f"Short switch (<30s) in dev cluster: {from_tool} → {to_tool}"
                else:
                    penalty = score_config.get('SHORT_SWITCH_NON_DEV_PENALTY_UNDER_30', -10)
                    reason = f"Short switch (<30s) outside dev cluster: {from_tool} → {to_tool}"

            total_score += penalty
            components.append(("Short Switch", penalty, reason))

        # Count cluster switches (from dev to non-dev or vice versa)
        if from_dev != to_dev:
            task_switches += 1

    # Optionally penalize cluster switches
    if task_switches > 0:
        switch_penalty = task_switches * score_config.get('CLUSTER_SWITCH_PENALTY', -2)
        components.append((
            "Task Switches",
            switch_penalty,
            f"{task_switches} cluster switches"
        ))
        total_score += switch_penalty

    # Reward extended focus intervals
    for duration in metrics['durations']:
        bracket_award = 0
        bracket_reason = None

        if duration >= 1200:
            bracket_award = score_config.get('EXTENDED_FOCUS_REWARD', 20) + ((duration - 1200) // 60)
            # every minute after 20 mins gets a point rewarding long focus sessions
        elif duration >= 600:  # 10+ minutes
            bracket_award = score_config.get('EXTENDED_FOCUS_REWARD', 20)
            bracket_reason = "Sustained focus over 10m"
        elif duration >= 300:  # 5+ minutes
            bracket_award = score_config.get('DEEP_FOCUS_REWARD', 15)
            bracket_reason = "Sustained focus over 5m"
        elif duration >= 180:  # 3+ minutes
            bracket_award = score_config.get('FOCUS_PERIOD_REWARD', 10)
            bracket_reason = "Sustained focus over 3m"

        # Only award the highest bracket reached for each block
        if bracket_award != 0 and bracket_reason:
            total_score += bracket_award
            components.append(("Focus Period", bracket_award, bracket_reason))

    return components, total_score

def get_score_emoji(score: float) -> str:
    """Return an appropriate emoji based on the focus score."""
    if score >= 100:
        return "🌟"    # Outstanding
    elif score >= 70:
        return "✨"    # Excellent
    elif score >= 40:
        return "😊"    # Good
    elif score >= 0:
        return "😐"    # Neutral/baseline
    elif score >= -40:
        return "😫"    # Poor
    elif score >= -70:
        return "😵"    # Very poor
    elif score >= -100:
        return "😱"    # Critical
    else:
        return "🤮"    # Beyond critical

from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional
from .utils import extract_domain


class ActivityAnalyzer:
    """Analyzes activity data"""

    def __init__(self):
        self.activity_duration = defaultdict(int)

    def update_duration(
        self,
        app_name: str,
        window_title: Optional[str],
        url: Optional[str],
        duration: float,
    ) -> None:
        """Update duration for an activity."""
        # Skip updating duration for idle time
        if app_name == "Idle":
            return

        # Use domain for browser activities, app name for others
        activity_key = extract_domain(url) if url else app_name
        if activity_key:
            self.activity_duration[activity_key] += duration

    def calculate_top_activities(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Calculate and return the top activities by duration."""
        total_time = sum(self.activity_duration.values())
        if total_time == 0:
            return []

        sorted_activities = sorted(
            self.activity_duration.items(), key=lambda x: x[1], reverse=True
        )
        top_n = sorted_activities[:limit]

        return [
            (activity, (duration / total_time) * 100) for activity, duration in top_n
        ]

    def get_activity_stats(self) -> Dict[str, Any]:
        """Get comprehensive activity statistics."""
        total_time = sum(self.activity_duration.values())

        stats = {
            "total_duration": total_time,
            "activity_count": len(self.activity_duration),
            "top_activities": self.calculate_top_activities(),
            "all_activities": dict(self.activity_duration),
        }

        return stats

    def reset(self) -> None:
        """Reset all durations."""
        self.activity_duration.clear()

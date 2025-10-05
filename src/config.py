"""Configuration for the Time Tracker."""

from pathlib import Path

# Database configuration
DB_DIR = Path.home() / ".lockedin"
DB_PATH = DB_DIR / "lockedin.db"

# Polling configuration
POLL_INTERVAL_SECONDS = 1.0

# Check-in configuration
CHECKIN_INTERVAL_MINUTES = 15

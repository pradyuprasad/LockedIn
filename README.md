# LockedIn - Personal Activity & Focus Tracker for macOS

LockedIn is a productivity suite for macOS that combines activity tracking, focus sessions, and detailed analytics to help you understand and optimize your computer usage patterns.

## Features

- **Activity Tracking**: Monitor active applications and web browsing in real-time
- **Focus Sessions**: Maintain concentration with customizable focus rules and real-time scoring
- **Rich Visualizations**: View your activity patterns through timelines and summaries
- **Session Management**: Create and track named work sessions
- **Database-Driven**: Reliable SQLite storage with timezone awareness

## Prerequisites

- macOS
- Python 3.10 or later
- UV package manager

## Quick Start

1. **Install UV** (if not already installed):
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and Setup**
```
git clone https://github.com/pradyuprasad/LockedIn.git
cd LockedIn
uv sync  # Install dependencies
```

3. **Initialize Database**
```
uv run db_setup.py
```

# **Important**: Core Tracking Process

**The main tracking process MUST be running for all other features to work!**

1. Start the tracker in a dedicated terminal window:
```
uv run main.py start
```

2. Keep this process running in the background while using other features
3. Control the tracking session using:
   1. n: Start a new named session
   2. s: Stop current session
   3. q: Quit tracking

# Features (Requires main.py running)
## Focus Mode
Start focus mode in a new terminal window:
```
uv run focus.py start
```

Features:

- Real-time focus score
- Distraction monitoring
- Session statistics

## Activity Visualization
View activity summary (in a new terminal window):
```
uv run activity_viz.py summary --hours 2  # Last 2 hours
uv run activity_viz.py summary --minutes 30  # Last 30 minutes
```

View activity timeline:
```
uv run activity_viz.py timeline --hours 1  # Last hour timeline
```

Watch live timeline updates:
```
uv run watch_timeline.py  # Auto-refreshes every 10 seconds
```

# Example Workflow
1. Start Core Tracking (Terminal 1):
```
uv run main.py start
# Keep this running!
```

2. Start Focus Session (Terminal 2):
```
uv run focus.py start
```

3. Monitor Activity (Terminal 3):
```
uv run watch_timeline.py
```

4. Check Summary (Terminal 4):
```
uv run activity_viz.py summary --hours 2
```

# Configuration
## Focus Mode Settings

Edit focus_config.yml to customize:

- Whitelisted apps and domains
- Blacklisted distractions

## Database Management
```
uv run db_setup.py
```

# Component Overview

* **main.py**: **Essential** core tracking engine - must be running for other features to work
* **focus.py**: Focus session manager with real-time scoring
* **activity_viz.py**: Activity visualization and reporting tools
* **watch_timeline.py**: Live activity timeline viewer
* **db_setup.py**: Database initialization and schema management
* **tracker.db**: SQLite database storing all activity data

# Troubleshooting

If visualization or focus features aren't working:
1. Ensure main.py is running in a terminal window
2. Check tracker.db exists and has recent data
3. Restart main.py if needed

# Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

# Author

Pradyumna

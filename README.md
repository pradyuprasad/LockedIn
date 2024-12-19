# LockedIn - Personal Activity Tracker for macOS

LockedIn is a personal activity tracking application designed for macOS that captures application usage and web activities. It provides insightful summaries and reports to help you understand how you spend your time on your computer.

## Features

- **Real-time Activity Tracking**: Monitors and records active applications and visited URLs.
- **Activity Summarization**: Offers detailed summaries for specified time periods (hours or minutes).
- **Timezone Conversion**: Converts UTC timestamps to your local timezone for more relevant insights.
- **Database Management**: SQLite database handles all activity records effortlessly.

## Prerequisites

- **macOS**
- **Python 3.10 or later**
- **uv** (for managing Python dependencies)

## Installation

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/pradyuprasad/LockedIn.git
    cd LockedIn
    ```

2. **Install uv** (if you haven't already):
   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

1. **Install Dependencies and set up the shell**:
    ```sh
    uv sync
    ```

4. **Set Up the Database**:
    ```sh
    uv run db_setup.py
    ```

5. **Run the Tracker**:
    ```sh
    uv run main.py start
    ```

## Usage

### Create DBs
First run `uv run db_setup.py`
### Start Tracking

To start tracking your application and web usage, run the `main.py` script. This script will continuously log your active applications and URLs into the database.

### Generate Activity Summary

To generate a summary of your activity over the past specified time period, use the `activity_viz.py` script. You can summarize by hours or minutes:
```sh
uv run python activity_viz.py summary --hours 1  # for the last hour
uv run python activity_viz.py summary --minutes 30  # for the last 30 minutes
```

### Session Management
While tracking is running, you can use the following keyboard commands:
- `n`: Start a new session (you'll be prompted to enter a session name)
- `s`: Stop the current session
- `q`: Quit tracking completely

### Convert Timestamps

If you need to convert UTC timestamps in the database to your local timezone, run:
```sh
python conversion_script.py
```

## File Descriptions

- **`main.py`**: The main tracking script that logs application and URL usage.
- **`activity_viz.py`**: Provides activity summaries for specified time periods.
- **`conversion_script.py`**: Converts timestamps in the database to the local timezone.
- **`db_setup.py`**: Creates the SQLite database and activities table.
- **`tracker.db`**: SQLite database that stores all activity logs.

## Example Commands

To get an activity summary for the last 2 hours:

```sh
uv run python activity_viz.py summary --hours 2
```

To convert all timestamps in `tracker.db` to the local timezone:

```sh
uv run python conversion_script.py
```

## Author

Pradyumna


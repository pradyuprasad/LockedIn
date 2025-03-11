import sqlite3
from typing import Optional, List, Tuple, Any
from datetime import datetime


class DatabaseManager:
    """Handles all database operations for the activity tracker"""

    def __init__(self, db_path="tracker.db"):
        self.db_path = db_path

    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

    def setup_database(self):
        """Initialize the database with all required tables and columns"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create the activities table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            app_name TEXT NOT NULL,
            window_title TEXT,
            url TEXT,
            session TEXT
        )
        """)

        # Ensure the session column exists (for backward compatibility)
        self._add_column(cursor, "activities", "session", "TEXT")

        conn.commit()
        conn.close()
        print("Database setup completed successfully.")

    def _add_column(self, cursor, table_name: str, column_name: str, column_type: str):
        """Private helper to add a column to a table if it doesn't exist"""
        # Check if the column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [column[1] for column in cursor.fetchall()]

        if column_name not in existing_columns:
            # Add the column if it doesn't exist
            alter_query = (
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            )
            cursor.execute(alter_query)
            print(f"Column '{column_name}' added to table '{table_name}'.")
        else:
            print(f"Column '{column_name}' already exists in table '{table_name}'.")

    def get_activities(
        self, start_time: datetime, end_time: Optional[datetime] = None
    ) -> List[Tuple[Any, ...]]:
        """Get activities within a time range"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT *
        FROM activities
        WHERE timestamp >= ?
        """
        params = [start_time.strftime("%Y-%m-%d %H:%M:%S")]

        if end_time:
            query += " AND timestamp < ?"
            params.append(end_time.strftime("%Y-%m-%d %H:%M:%S"))

        query += " ORDER BY timestamp"

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def insert_activity(
        self, timestamp, app_name, window_title, url, session_name=None
    ):
        """Insert an activity record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
        INSERT INTO activities (timestamp, app_name, window_title, url, session)
        VALUES (?, ?, ?, ?, ?)
        """,
            (timestamp, app_name, window_title, url, session_name),
        )
        conn.commit()
        conn.close()

    def get_latest_activity(self):
        """Get the most recent activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT timestamp, app_name, url
        FROM activities
        ORDER BY timestamp DESC
        LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        return result

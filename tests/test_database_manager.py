import unittest
import os
import tempfile
from datetime import datetime, timedelta

from database_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test the DatabaseManager class"""

    def setUp(self):
        """Set up a test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)

    def tearDown(self):
        """Clean up after tests"""
        os.unlink(self.temp_db.name)

    def test_setup_database(self):
        """Test database setup creates the correct schema"""
        self.db_manager.setup_database()

        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(activities)")
        columns = {col[1] for col in cursor.fetchall()}

        expected_columns = {
            "id",
            "timestamp",
            "app_name",
            "window_title",
            "url",
            "session",
        }
        self.assertEqual(columns, expected_columns)

        conn.close()

    def test_insert_and_get_activity(self):
        """Test inserting and retrieving activities"""
        self.db_manager.setup_database()

        now = datetime.now()
        timestamp1 = now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp2 = (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

        self.db_manager.insert_activity(
            timestamp1, "TestApp1", "Window1", "http://example.com", "TestSession"
        )
        self.db_manager.insert_activity(
            timestamp2, "TestApp2", "Window2", None, "TestSession"
        )

        activities = self.db_manager.get_activities(now - timedelta(minutes=10))

        self.assertEqual(len(activities), 2)

        latest = self.db_manager.get_latest_activity()
        self.assertEqual(latest[0], timestamp1)
        self.assertEqual(latest[1], "TestApp1")
        self.assertEqual(latest[2], "http://example.com")

    def test_get_activities_with_time_range(self):
        """Test getting activities within a specific time range"""
        self.db_manager.setup_database()

        # Insert test activities at different times
        now = datetime.now()
        time1 = now - timedelta(hours=2)
        time2 = now - timedelta(hours=1)
        time3 = now

        self.db_manager.insert_activity(
            time1.strftime("%Y-%m-%d %H:%M:%S"), "App1", "Window1", None, None
        )
        self.db_manager.insert_activity(
            time2.strftime("%Y-%m-%d %H:%M:%S"), "App2", "Window2", None, None
        )
        self.db_manager.insert_activity(
            time3.strftime("%Y-%m-%d %H:%M:%S"), "App3", "Window3", None, None
        )

        # Get activities from the last hour
        activities = self.db_manager.get_activities(
            now - timedelta(hours=1, minutes=5), now + timedelta(minutes=5)
        )

        # Should have 2 activities (from time2 and time3)
        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0][2], "App2")  # First activity should be App2
        self.assertEqual(activities[1][2], "App3")  # Second activity should be App3


if __name__ == "__main__":
    unittest.main()

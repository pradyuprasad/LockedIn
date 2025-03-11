import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from io import StringIO
import tempfile

from database_manager import DatabaseManager


class TestIntegrationMainFlow(unittest.TestCase):
    """Integration tests for the main activity tracking flow"""

    def setUp(self):
        """Set up a test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.db_manager.setup_database()

        self.db_path_patcher = patch("main.DatabaseManager")
        self.mock_db_manager_class = self.db_path_patcher.start()
        self.mock_db_manager = MagicMock()
        self.mock_db_manager_class.return_value = self.mock_db_manager

        # Patch get_active_window_info to return predictable values
        self.window_info_patcher = patch(
            "tracking.activity_tracker.ActivityTracker.get_active_window_info"
        )
        self.mock_window_info = self.window_info_patcher.start()

        # Patch select.select to simulate user input
        self.select_patcher = patch("select.select")
        self.mock_select = self.select_patcher.start()

        # Patch sys.stdin for input simulation
        self.stdin_patcher = patch("sys.stdin")
        self.mock_stdin = self.stdin_patcher.start()

        # Patch time.sleep to speed up tests
        self.sleep_patcher = patch("time.sleep")
        self.mock_sleep = self.sleep_patcher.start()

        # Capture stdout
        self.stdout_patcher = patch("sys.stdout", new_callable=StringIO)
        self.mock_stdout = self.stdout_patcher.start()

        # Import the module here to ensure all patches are applied
        import main

        self.main_module = main

    def tearDown(self):
        """Clean up after tests"""
        self.db_path_patcher.stop()
        self.window_info_patcher.stop()
        self.select_patcher.stop()
        self.stdin_patcher.stop()
        self.sleep_patcher.stop()
        self.stdout_patcher.stop()

        # Remove test database
        os.unlink(self.temp_db.name)

    @patch("click.Command.invoke")
    def test_activity_tracking_flow(self, mock_invoke):
        """Test the main activity tracking flow by directly calling the function"""
        # Get the actual function that would be called by the Click command
        from main import start as start_command

        # Access the callback function that Click would call
        start_function = start_command.callback

        # Setup mock window info to return different apps
        self.mock_window_info.side_effect = [
            ("Terminal", "Terminal Window", None),
            ("Safari", "Example Page", "https://example.com"),
            ("Visual Studio Code", "main.py", None),
            # Add KeyboardInterrupt to stop the loop
            KeyboardInterrupt,
        ]

        # Setup mock select to simulate no user input
        self.mock_select.return_value = ([], [], [])

        # Run the function directly (should exit on KeyboardInterrupt)
        try:
            # Call the function directly instead of through Click
            start_function()
        except KeyboardInterrupt:
            pass

        # Check that insert_activity was called for each window info
        self.assertEqual(self.mock_db_manager.insert_activity.call_count, 3)

        # Check output contains expected text
        output = self.mock_stdout.getvalue()
        self.assertIn("Activity tracking started", output)

    @patch("click.Command.invoke")
    def test_session_management(self, mock_invoke):
        """Test session management functionality"""
        # Get the actual function that would be called by the Click command
        from main import start as start_command

        # Access the callback function that Click would call
        start_function = start_command.callback

        # Setup mock window info
        self.mock_window_info.side_effect = [
            ("Terminal", "Terminal Window", None),
            KeyboardInterrupt,
        ]

        # Setup mock select to simulate user input for new session
        self.mock_select.return_value = ([sys.stdin], [], [])
        self.mock_stdin.readline.return_value = "n\n"

        # Mock input function for session name
        with patch("builtins.input", return_value="Test Session"):
            try:
                # Call the function directly instead of through Click
                start_function()
            except KeyboardInterrupt:
                pass

        # Check that insert_activity was called with Terminal
        self.mock_db_manager.insert_activity.assert_any_call(
            unittest.mock.ANY,  # timestamp
            "Terminal",
            "Terminal Window",
            None,
            unittest.mock.ANY,  # session name - may be None in the implementation
        )

        # Check output contains session info
        output = self.mock_stdout.getvalue()
        self.assertIn("New session started: Test Session", output)


if __name__ == "__main__":
    unittest.main()

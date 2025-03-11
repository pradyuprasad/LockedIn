import unittest
from unittest.mock import patch, MagicMock
import time
from io import StringIO
from collections import defaultdict
import subprocess

# Import the functions and classes we want to test
from main import (
    format_elapsed_time,
    extract_domain,
    run_applescript,
    get_browser_info,
    get_window_title,
    get_active_window_info,
    insert_activity,
    calculate_top_activities,
    display_top_activities,
)


class TestUtilityFunctions(unittest.TestCase):
    """Test the utility functions in main.py"""

    def test_format_elapsed_time(self):
        """Test the format_elapsed_time function with various inputs"""
        self.assertEqual(format_elapsed_time(30), "30s")
        self.assertEqual(format_elapsed_time(90), "1m 30s")
        self.assertEqual(format_elapsed_time(3600), "1h 0s")
        self.assertEqual(format_elapsed_time(3661), "1h 1m 1s")
        self.assertEqual(format_elapsed_time(86400 + 3661), "1d 1h 1m 1s")

    def test_extract_domain(self):
        """Test the extract_domain function with various URLs"""
        self.assertEqual(extract_domain("https://www.example.com/page"), "example.com")
        self.assertEqual(extract_domain("http://example.com"), "example.com")
        self.assertEqual(
            extract_domain("https://subdomain.example.com/path?query=1"),
            "subdomain.example.com",
        )
        result = extract_domain("not a url")
        self.assertTrue(result is None or result == "")


class TestAppleScriptFunctions(unittest.TestCase):
    """Test the AppleScript-related functions"""

    @patch("subprocess.run")
    def test_run_applescript_success(self, mock_run):
        """Test run_applescript when subprocess succeeds"""
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_applescript("test script")
        mock_run.assert_called_with(
            ["osascript", "-e", "test script"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result, "test output")

    @patch("subprocess.run")
    def test_run_applescript_failure(self, mock_run):
        """Test run_applescript when subprocess fails"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "osascript", "Error")

        result = run_applescript("test script")
        self.assertIsNone(result)

    @patch("main.run_applescript")
    def test_get_browser_info(self, mock_run_applescript):
        """Test get_browser_info function"""
        mock_run_applescript.return_value = "https://example.com|Example Page"

        url, title = get_browser_info("Safari")
        mock_run_applescript.assert_called_once()
        self.assertEqual(url, "https://example.com")
        self.assertEqual(title, "Example Page")

        # Test when AppleScript fails
        mock_run_applescript.return_value = None
        url, title = get_browser_info("Safari")
        self.assertIsNone(url)
        self.assertIsNone(title)

    @patch("main.run_applescript")
    def test_get_window_title(self, mock_run_applescript):
        """Test get_window_title function"""
        mock_run_applescript.return_value = "Test Window"

        title = get_window_title("TestApp")
        mock_run_applescript.assert_called_once()
        self.assertEqual(title, "Test Window")

        # Test when AppleScript fails
        mock_run_applescript.return_value = None
        title = get_window_title("TestApp")
        self.assertEqual(title, "No window title available")


class TestActivityTracking(unittest.TestCase):
    """Test the activity tracking functionality"""

    @patch("main.NSWorkspace")
    @patch("main.get_browser_info")
    @patch("main.get_window_title")
    def test_get_active_window_info(
        self, mock_get_window_title, mock_get_browser_info, mock_workspace
    ):
        """Test get_active_window_info function"""
        # Setup mock for NSWorkspace
        mock_shared = MagicMock()
        mock_workspace.sharedWorkspace.return_value = mock_shared

        # Test browser app
        mock_shared.activeApplication.return_value = {"NSApplicationName": "Safari"}
        mock_get_browser_info.return_value = ("https://example.com", "Example Page")

        app_name, title, url = get_active_window_info()
        self.assertEqual(app_name, "Safari")
        self.assertEqual(title, "Example Page")
        self.assertEqual(url, "https://example.com")

        # Test non-browser app
        mock_shared.activeApplication.return_value = {"NSApplicationName": "Terminal"}
        mock_get_window_title.return_value = "Terminal Window"

        app_name, title, url = get_active_window_info()
        self.assertEqual(app_name, "Terminal")
        self.assertEqual(title, "Terminal Window")
        self.assertIsNone(url)

        # Test idle state
        mock_shared.activeApplication.return_value = {
            "NSApplicationName": "loginwindow"
        }

        app_name, title, url = get_active_window_info()
        self.assertEqual(app_name, "Idle")
        self.assertEqual(title, "Computer Off")
        self.assertIsNone(url)

        # Test exception handling
        mock_shared.activeApplication.side_effect = Exception("Test error")

        app_name, title, url = get_active_window_info()
        self.assertIsNone(app_name)
        self.assertIsNone(title)
        self.assertIsNone(url)


class TestActivityAnalysis(unittest.TestCase):
    """Test the activity analysis functionality"""

    def setUp(self):
        """Reset the activity_duration global before each test"""
        # This is a bit hacky but necessary since we're testing with globals
        import main

        main.activity_duration = defaultdict(int)

    def test_insert_activity(self):
        """Test insert_activity function"""
        db_manager = MagicMock()
        timestamp = "2023-01-01 12:00:00"
        previous_time = time.time() - 60  # 60 seconds ago

        # Test with browser URL
        insert_activity(
            db_manager,
            timestamp,
            "Safari",
            "Example Page",
            "https://example.com",
            None,
            previous_time,
        )
        db_manager.insert_activity.assert_called_with(
            timestamp, "Safari", "Example Page", "https://example.com", None
        )

        # Check activity_duration was updated
        import main

        self.assertGreater(
            main.activity_duration["example.com"], 59
        )  # At least 59 seconds

        # Test with app name
        main.activity_duration = defaultdict(int)
        insert_activity(
            db_manager,
            timestamp,
            "Terminal",
            "Terminal Window",
            None,
            None,
            previous_time,
        )
        self.assertGreater(main.activity_duration["Terminal"], 59)

    def test_calculate_top_activities(self):
        """Test calculate_top_activities function"""
        import main

        main.activity_duration = {
            "app1": 100,
            "app2": 200,
            "app3": 50,
            "app4": 300,
            "app5": 150,
            "app6": 25,
        }

        top_activities = calculate_top_activities()

        # Should return top 5 activities
        self.assertEqual(len(top_activities), 5)

        # Should be sorted by duration
        self.assertEqual(top_activities[0][0], "app4")
        self.assertEqual(top_activities[1][0], "app2")
        self.assertEqual(top_activities[2][0], "app5")

        # Should include percentage
        total_time = 825  # Sum of all durations
        self.assertAlmostEqual(top_activities[0][1], (300 / total_time) * 100)

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_top_activities(self, mock_stdout):
        """Test display_top_activities function"""
        activities = [("app1", 50.0), ("app2", 30.0), ("app3", 20.0)]

        display_top_activities(activities)
        output = mock_stdout.getvalue()

        self.assertIn("Top 5 Activities:", output)
        self.assertIn("app1: 50.00%", output)
        self.assertIn("app2: 30.00%", output)
        self.assertIn("app3: 20.00%", output)

        # Test with empty list
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        display_top_activities([])
        output = mock_stdout.getvalue()
        self.assertIn("No activities to display.", output)


if __name__ == "__main__":
    unittest.main()

"""Tests for macOS activity poller."""

from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
import subprocess
from src.polling.mac_poller import MacOSPoller, Browser
from src.models import ActivitySnapshot


class TestMacOSPoller:
    """Test suite for MacOSPoller."""

    @pytest.fixture
    def poller(self):
        """Create a MacOSPoller instance for testing.

        Returns:
            MacOSPoller instance.
        """
        return MacOSPoller()

    @patch('src.polling.mac_poller.subprocess.run')
    def test_poll_once_with_browser(self, mock_run, poller):
        """Test poll_once captures activity from a browser correctly.

        Args:
            mock_run: Mocked subprocess.run function.
            poller: MacOSPoller fixture.
        """
        # Mock AppleScript responses
        mock_run.side_effect = [
            MagicMock(stdout="Google Chrome\n"),  # _get_active_app
            MagicMock(stdout="GitHub - Browser\n"),  # _get_window_title
            MagicMock(stdout="https://github.com/user/repo\n"),  # _get_browser_url
        ]

        snapshot = poller.poll_once()

        assert isinstance(snapshot, ActivitySnapshot)
        assert snapshot.app_name == "Google Chrome"
        assert snapshot.window_title == "GitHub - Browser"
        assert snapshot.url == "https://github.com/user/repo"
        assert snapshot.domain == "github.com"
        assert isinstance(snapshot.timestamp, datetime)

    @patch('src.polling.mac_poller.subprocess.run')
    def test_poll_once_with_non_browser(self, mock_run, poller):
        """Test poll_once captures activity from non-browser app correctly.

        Args:
            mock_run: Mocked subprocess.run function.
            poller: MacOSPoller fixture.
        """
        # Mock AppleScript responses
        mock_run.side_effect = [
            MagicMock(stdout="VSCode\n"),  # _get_active_app
            MagicMock(stdout="main.py - VSCode\n"),  # _get_window_title
        ]

        snapshot = poller.poll_once()

        assert snapshot.app_name == "VSCode"
        assert snapshot.window_title == "main.py - VSCode"
        assert snapshot.url is None
        assert snapshot.domain is None

    def test_is_browser_recognizes_all_browsers(self, poller):
        """Test that all supported browsers are recognized.

        Args:
            poller: MacOSPoller fixture.
        """
        for browser in Browser:
            assert poller._is_browser(browser.value) is True

    def test_is_browser_rejects_non_browsers(self, poller):
        """Test that non-browser apps are not recognized as browsers.

        Args:
            poller: MacOSPoller fixture.
        """
        assert poller._is_browser("VSCode") is False
        assert poller._is_browser("Terminal") is False
        assert poller._is_browser("Slack") is False

    def test_extract_domain(self, poller):
        """Test domain extraction from various URLs.

        Args:
            poller: MacOSPoller fixture.
        """
        assert poller._extract_domain("https://github.com/user/repo") == "github.com"
        assert poller._extract_domain("http://localhost:8000/test") == "localhost:8000"
        assert poller._extract_domain("https://docs.python.org/3/library/") == "docs.python.org"

    @patch('src.polling.mac_poller.subprocess.run')
    def test_get_browser_url_handles_chromium_browsers(self, mock_run, poller):
        """Test URL retrieval for Chromium-based browsers.

        Args:
            mock_run: Mocked subprocess.run function.
            poller: MacOSPoller fixture.
        """
        chromium_browsers = [Browser.CHROME, Browser.ARC, Browser.BRAVE]

        for browser in chromium_browsers:
            mock_run.return_value = MagicMock(stdout="https://example.com\n")
            url = poller._get_browser_url(browser.value)
            assert url == "https://example.com"

    @patch('src.polling.mac_poller.subprocess.run')
    def test_get_browser_url_handles_safari(self, mock_run, poller):
        """Test URL retrieval for Safari.

        Args:
            mock_run: Mocked subprocess.run function.
            poller: MacOSPoller fixture.
        """
        mock_run.return_value = MagicMock(stdout="https://apple.com\n")
        url = poller._get_browser_url(Browser.SAFARI.value)
        assert url == "https://apple.com"

    def test_get_browser_url_returns_none_for_firefox(self, poller):
        """Test that Firefox returns None (limited AppleScript support).

        Args:
            poller: MacOSPoller fixture.
        """
        url = poller._get_browser_url(Browser.FIREFOX.value)
        assert url is None

    @patch('src.polling.mac_poller.subprocess.run')
    def test_get_browser_url_handles_errors_gracefully(self, mock_run, poller):
        """Test that AppleScript errors are handled gracefully.

        Args:
            mock_run: Mocked subprocess.run function.
            poller: MacOSPoller fixture.
        """
        mock_run.side_effect = subprocess.CalledProcessError(1, "osascript")
        url = poller._get_browser_url(Browser.CHROME.value)
        assert url is None

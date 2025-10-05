#!/usr/bin/env python3
"""Manual test script for MacOSPoller.

Run this script to see the poller capture your current activity in real-time.
"""

import time
from src.polling.mac_poller import MacOSPoller


def main():
    """Run the poller a few times and print results."""
    poller = MacOSPoller()

    print("Testing MacOSPoller - capturing activity 5 times (1 second apart)\n")
    print("=" * 80)

    for i in range(5):
        print(f"\nCapture #{i + 1}:")
        print("-" * 80)

        try:
            snapshot = poller.poll_once()
            print(f"Timestamp:     {snapshot.timestamp}")
            print(f"App Name:      {snapshot.app_name}")
            print(f"Window Title:  {snapshot.window_title}")
            print(f"URL:           {snapshot.url or 'N/A'}")
            print(f"Domain:        {snapshot.domain or 'N/A'}")
        except Exception as e:
            print(f"Error: {e}")

        if i < 4:  # Don't sleep after last iteration
            time.sleep(1)

    print("\n" + "=" * 80)
    print("Test complete!")


if __name__ == "__main__":
    main()

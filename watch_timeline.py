import time
import os
from activity_viz import timeline


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


REFRESH_INTERVAL = 10  # seconds

while True:
    clear_screen()
    print(f"Updates every {REFRESH_INTERVAL} seconds...")
    print()
    timeline.callback(hours=6, minutes=None)
    time.sleep(REFRESH_INTERVAL)

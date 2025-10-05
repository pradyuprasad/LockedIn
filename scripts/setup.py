"""Setup script to initialize the database."""

import sys
from pathlib import Path
import sqlite3

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_DIR, DB_PATH
from src.schema import SCHEMA
from src.logging import setup_logging, get_logger



def setup():
    """Create database directory, initialize schema."""
    setup_logging()
    _logger = get_logger(name=__name__)
    # Create directory if it doesn't exist
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Create database and schema
    _logger.info(f"Creating database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    print("Database initialized successfully!")


if __name__ == "__main__":
    setup()

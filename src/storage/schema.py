"""Database schema for SQLite storage."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp DATETIME NOT NULL,
    app_name TEXT NOT NULL,
    window_title TEXT NOT NULL,
    url TEXT,
    domain TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Sessions: organizational metadata
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    goal TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME
);
"""

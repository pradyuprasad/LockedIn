import sqlite3

def create_database():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()

    # Create the activities table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        app_name TEXT NOT NULL,
        window_title TEXT,
        url TEXT
    )
    ''')

    conn.commit()
    conn.close()

    print("Database and table created successfully.")

if __name__ == "__main__":
    create_database()

import sqlite3

def get_db_connection():
    return sqlite3.connect('tracker.db')

def add_column(cursor, table_name, column_name, column_type):
    # Check if the column exists
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    if column_name not in existing_columns:
        # Add the column if it doesn't exist
        alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        cursor.execute(alter_query)
        print(f"Column '{column_name}' added to table '{table_name}'.")
    else:
        print(f"Column '{column_name}' already exists in table '{table_name}'.")

def create_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the activities table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        app_name TEXT NOT NULL,
        window_title TEXT,
        url TEXT
    )
    ''')

    # Add the new session column
    add_column(cursor, "activities", "session", "TEXT")

    conn.commit()
    conn.close()
    print("Database setup completed successfully.")

if __name__ == "__main__":
    create_database()

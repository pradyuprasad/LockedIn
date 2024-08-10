import sqlite3
from datetime import datetime
import pytz

def convert_timestamps():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()

    # Define the local timezone
    local_tz = pytz.timezone('Asia/Singapore')

    # Fetch all records
    cursor.execute('SELECT id, timestamp FROM activities')
    records = cursor.fetchall()

    for record in records:
        record_id, utc_timestamp = record
        
        # Convert the UTC timestamp to a datetime object
        utc_dt = datetime.strptime(utc_timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Set the timezone to UTC and then convert to local time
        utc_dt = pytz.utc.localize(utc_dt)
        local_dt = utc_dt.astimezone(local_tz)
        local_time = local_dt.strftime('%Y-%m-%d %H:%M:%S')

        # Update the record with the local time
        cursor.execute('UPDATE activities SET timestamp = ? WHERE id = ?', (local_time, record_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    convert_timestamps()

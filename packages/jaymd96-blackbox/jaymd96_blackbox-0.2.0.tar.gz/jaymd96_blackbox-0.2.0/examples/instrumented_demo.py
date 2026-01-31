"""
Demo script that exercises multiple instrumentation features.

Run with: python -m blackbox examples/instrumented_demo.py
"""

import os
import time
import sqlite3
import tempfile


def fetch_data():
    """Simulates an HTTP-like operation."""
    # This would normally use requests/httpx
    # For demo purposes, just do some file I/O
    time.sleep(0.05)  # Simulate network latency
    return {"status": "ok", "data": [1, 2, 3]}


def setup_database():
    """Create a temporary SQLite database."""
    db_file = tempfile.mktemp(suffix='.db')
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    ''')

    cursor.execute('INSERT INTO users (name, email) VALUES (?, ?)',
                   ('Alice', 'alice@example.com'))
    cursor.execute('INSERT INTO users (name, email) VALUES (?, ?)',
                   ('Bob', 'bob@example.com'))

    conn.commit()
    return conn


def query_users(conn, user_id):
    """Query the database for a user."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()


def read_config():
    """Read environment configuration."""
    api_key = os.getenv('API_KEY', 'default-key')
    debug_mode = os.getenv('DEBUG', 'false')
    return {
        'api_key': api_key,
        'debug': debug_mode.lower() == 'true',
    }


def process_data(data):
    """Process the data - this will crash!"""
    # Allocate some memory
    large_list = [i * 2 for i in range(10000)]

    # Access a key that doesn't exist
    result = data['missing_key']  # This will raise KeyError
    return result


def main():
    """Main function that ties everything together."""
    print("Starting instrumented demo...")

    # Read config (triggers env access)
    config = read_config()
    print(f"Config loaded: debug={config['debug']}")

    # Set up database
    conn = setup_database()
    print("Database created")

    # Query some data
    user = query_users(conn, 1)
    print(f"Found user: {user}")

    # Simulate HTTP fetch
    response = fetch_data()
    print(f"Fetched data: {response}")

    # This will crash
    result = process_data(response)
    print(f"Processed: {result}")

    conn.close()


if __name__ == '__main__':
    main()

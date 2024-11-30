import sqlite3
from datetime import datetime

SQLITE_DB = "app.db"

def db_init():
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            routine_type TEXT NOT NULL,
            date_time DATETIME NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balance (
            user_name TEXT PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')

    connection.commit()
    connection.close()

def insert_streak(user_name, routine_type):
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    local_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
    INSERT INTO streaks (user_name, routine_type, date_time)
    VALUES (?, ?, ?)
    ''', (user_name, routine_type, local_datetime))

    connection.commit()
    connection.close()

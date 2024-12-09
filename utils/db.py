import sqlite3
from datetime import datetime, timedelta

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

def insert_streak(user_name, command_package):
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    routine_type = command_package.command_name
    local_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO streaks (user_name, routine_type, date_time)
        VALUES (?, ?, ?)
    ''', (user_name, routine_type, local_datetime))

    connection.commit()
    connection.close()

def validate_streak(user_name, command_package):
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    punished = False
    punishment = command_package.get_criteria("punishment")
    query = command_package.get_criteria("validator")
    query = query(user_name)

    cursor.execute(query)
    records = cursor.fetchone()[0]

    if not records:
        punished = True
        cursor.execute('''
            INSERT OR REPLACE INTO balance (user_name, balance)
            VALUES (?, COALESCE((SELECT balance FROM balance WHERE user_name = ?), 0.0) + ?);
        ''', (user_name, user_name, punishment))

    connection.commit()
    connection.close()

    return punished

def summarize_streak(user_name):
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    # dont even ask lol...
    cursor.execute(f'''
        SELECT routine_type, COUNT(DISTINCT DATE(date_time)) AS unique_date_count
        FROM streaks
        WHERE strftime('%Y-%W', date_time) = strftime('%Y-%W', 'now', 'localtime')
        AND user_name = ?
        GROUP BY routine_type
    ''', (user_name,))

    records = cursor.fetchall()

    connection.commit()
    connection.close()

    return records

def get_users():
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    cursor.execute("SELECT DISTINCT user_name FROM balance")
    users = cursor.fetchall()
    users = [user[0] for user in users]

    connection.commit()
    connection.close()
    
    return users

def get_balance(user_name):
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    cursor.execute(f'''
        SELECT balance
        FROM balance
        WHERE user_name = ?;
    ''', (user_name,))

    balance = cursor.fetchone()
    
    if not balance:
        balance = 0.0
        cursor.execute('''
            INSERT INTO balance (user_name, balance)
            VALUES (?, ?);
        ''', (user_name, 0.0))
    else:
        balance = balance[0]

    connection.commit()
    connection.close()

    return balance

def change_balance(user_name, new_balance):
    connection = sqlite3.connect(SQLITE_DB)
    cursor = connection.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO balance (user_name, balance)
        VALUES (?, ?);
    ''', (user_name, new_balance))

    connection.commit()
    connection.close()
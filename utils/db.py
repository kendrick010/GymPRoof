from functools import wraps
import sqlite3

SQLITE_DB = "app.db"

def db_connection(func):
    # Database connection decorator
    @wraps(func)
    def wrapper(*args, **kwargs):
        connection = sqlite3.connect(SQLITE_DB)
        cursor = connection.cursor()

        try:
            result = func(cursor, *args, **kwargs)
            connection.commit()

        finally:
            connection.close()

        return result
    
    return wrapper

@db_connection
def db_init(cursor):
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

@db_connection
def add_streak(cursor, user_name, command_package):
    routine_type = command_package.command_name

    cursor.execute('''
        INSERT INTO streaks (user_name, routine_type, date_time)
        VALUES (?, ?, DATETIME('now', 'localtime'))
    ''', (user_name, routine_type))

@db_connection
def summarize_streak(cursor, user_name):
    cursor.execute(f'''
        SELECT routine_type, COUNT(DISTINCT DATE(date_time)) AS unique_date_count
        FROM streaks
        WHERE strftime('%Y-%W', date_time) = strftime('%Y-%W', 'now', 'localtime')
        AND user_name = ?
        GROUP BY routine_type
    ''', (user_name,))

    return cursor.fetchall()

@db_connection
def punish_user(cursor, user_name, command_package):
    punishment_amount = command_package.get_member("punishment")
    punishment_validator = command_package.get_member("validator")
    query = punishment_validator(user_name)

    cursor.execute(query)
    records = cursor.fetchone()[0]

    if not records:
        cursor.execute('''
            INSERT OR REPLACE INTO balance (user_name, balance)
            VALUES (?, COALESCE((SELECT balance FROM balance WHERE user_name = ?), 0.0) + ?);
        ''', (user_name, user_name, punishment_amount))

        return True

    return False

@db_connection
def get_users(cursor):
    cursor.execute('''
        SELECT DISTINCT user_name FROM balance
    ''')

    users = [user[0] for user in cursor.fetchall()]
    
    return users

@db_connection
def get_balance(cursor, user_name):
    cursor.execute('''
        INSERT OR IGNORE INTO balance (user_name) VALUES (?);
    ''', (user_name,))

    cursor.execute('''
        SELECT balance FROM balance WHERE user_name = ?;
    ''', (user_name,))

    user_balance = cursor.fetchone()[0]

    return user_balance

@db_connection
def change_balance(cursor, user_name, new_balance):
    cursor.execute('''
        INSERT OR REPLACE INTO balance (user_name, balance)
        VALUES (?, ?);
    ''', (user_name, new_balance))
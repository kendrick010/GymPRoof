from functools import wraps
import sqlite3
import json

from commands import CommandPackage

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
            user_id TEXT NOT NULL,
            routine_type TEXT NOT NULL,
            date_time DATETIME NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            user_balance REAL DEFAULT 0.0,
            opted_routines TEXT DEFAULT '[]'
        )
    ''')

@db_connection
def add_streak(cursor, user_id: str, command_package: CommandPackage):
    routine_type = command_package.command_name

    cursor.execute('''
        INSERT INTO streaks (user_id, routine_type, date_time)
        VALUES (?, ?, DATETIME('now', 'localtime'))
    ''', (user_id, routine_type))

@db_connection
def summarize_streak(cursor, user_id: str):
    cursor.execute(f'''
        SELECT routine_type, COUNT(DISTINCT DATE(date_time)) AS unique_date_count
        FROM streaks
        WHERE strftime('%Y-%W', date_time) = strftime('%Y-%W', 'now', 'localtime')
        AND user_id = ?
        GROUP BY routine_type
    ''', (user_id,))

    return cursor.fetchall()

@db_connection
def punish_user(cursor, user_id: str, command_package: CommandPackage):
    punishment_amount = command_package.get_member("punishment")
    validator_builder = command_package.get_member("validator")
    query = validator_builder(user_id)

    # Execute validation query
    cursor.execute(query)
    records = cursor.fetchone()[0]

    if not records:
        cursor.execute('''
            UPDATE users
            SET user_balance = user_balance + ?
            WHERE user_id = ?;
        ''', (punishment_amount, user_id))

        return True

    return False

@db_connection
def add_user(cursor, user_id: str):
    cursor.execute('''
        INSERT INTO users (user_id)
        VALUES (?);
    ''', (user_id,))

@db_connection
def get_users(cursor):
    cursor.execute('''
        SELECT DISTINCT user_id FROM users;
    ''')

    users = [user[0] for user in cursor.fetchall()]
    
    return users

@db_connection
def get_balance(cursor, user_id: str):
    cursor.execute('''
        SELECT user_balance FROM users WHERE user_id = ?;
    ''', (user_id,))

    user_balance = cursor.fetchone()[0]

    return user_balance

@db_connection
def update_balance(cursor, user_id: str, new_balance: float):
    cursor.execute('''
        UPDATE users 
        SET user_balance = ?
        WHERE user_id = ?;
    ''', (user_id, new_balance))

@db_connection
def update_opted_routine(cursor, user_id: str, command_package: CommandPackage):
    cursor.execute('''
        SELECT opted_routines FROM users WHERE user_id = ?;
    ''', (user_id,))

    queried_routines = cursor.fetchone()[0]

    # Enforce uniqueness
    opted_routines = json.loads(queried_routines)
    opted_routines = set(opted_routines)
    opted_routines.add(command_package.command_name)
    opted_routines = list(opted_routines)

    cursor.execute('''
        UPDATE users
        SET opted_routines = ?
        WHERE user_id = ?;
    ''', (json.dumps(opted_routines), user_id))

@db_connection
def drop_opted_routine(cursor, user_id: str, command_package: CommandPackage):
    cursor.execute('''
        SELECT opted_routines FROM users WHERE user_id = ?;
    ''', (user_id,))

    queried_routines = cursor.fetchone()[0]

    # Enforce uniqueness
    opted_routines = json.loads(queried_routines)
    opted_routines = set(opted_routines)
    opted_routines.discard(command_package.command_name)
    opted_routines = list(opted_routines)

    cursor.execute('''
        UPDATE users
        SET opted_routines = ?
        WHERE user_id = ?;
    ''', (json.dumps(opted_routines), user_id))

@db_connection
def get_opted_routines(cursor, user_id: str):
    cursor.execute('''
        SELECT opted_routines FROM users
        WHERE user_id = ?;
    ''', (user_id,))

    queried_routines = cursor.fetchone()[0]
    opted_routines = json.loads(queried_routines)
    
    return opted_routines

@db_connection
def get_opted_users(cursor, command_package: CommandPackage):
    routine_type = command_package.command_name

    cursor.execute('''
        SELECT user_id FROM users WHERE opted_routines LIKE ?";
    ''', (routine_type,))

    users = [user[0] for user in cursor.fetchall()]
    
    return users
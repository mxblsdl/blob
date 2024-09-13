import sqlite3
import secrets
import datetime

TOKEN_EXP_MINUTES = 30


# Create database connection
def get_db():
    db = sqlite3.connect("app/data/file_uploads.db", check_same_thread=False)
    db.row_factory = sqlite3.Row
    # db.set_trace_callback(print)
    try:
        yield db
    finally:
        db.commit()
        db.close()


# Initialize the database
def init_db():
    with sqlite3.connect("app/data/file_uploads.db") as db:
        cur = db.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
            )
        """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            folder_id INTEGER NOT NULL,
            bin BLOB NOT NULL,
            size INTEGER NOT NULL,
            created_at TEXT,
            FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOiNCREMENT,
            user_id INTEGER NOT NULL,
            parent_folder_id INTEGER,
            folder_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            is_login TEXT,
            key TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            )
        """
        )
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            file_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (file_id) REFERENCES data(id) ON DELETE CASCADE
        )"""
        )
        db.commit()


def generate_token():
    token = secrets.token_urlsafe(16)
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXP_MINUTES)
    return token, expires_at

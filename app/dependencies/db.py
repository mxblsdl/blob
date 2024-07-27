import sqlite3
import secrets
import datetime

TOKEN_EXP_MINUTES = 30


# Create database connection
def get_db():
    db = sqlite3.connect("data/file_uploads.db", check_same_thread=False)
    db.row_factory = sqlite3.Row
    # db.set_trace_callback(print)
    try:
        yield db
    finally:
        db.commit()
        db.close()


# Initialize the database
def init_db():
    with sqlite3.connect("data/file_uploads.db") as db:
        cur = db.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                user TEXT,
                bin BLOB NOT NULL,
                size INTEGER,
                created_at TEXT
            )
        """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
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


def generate_token(file_id: int):
    token = secrets.token_urlsafe(16)
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXP_MINUTES)

    with sqlite3.connect("data/file_uploads.db") as conn:
        conn.execute(
            """
        INSERT INTO tokens (token, file_id, expires_at)
        VALUES (?, ?, ?)
        """,
            (token, file_id, expires_at),
        )

    return token

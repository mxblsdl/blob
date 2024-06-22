import sqlite3
import secrets
import datetime
from contextlib import contextmanager

TOKEN_EXP_MINUTES = 30


# Create database connection
@contextmanager
def get_db():
    db = sqlite3.connect("file_uploads.db")
    db.set_trace_callback(print)
    try:
        yield db
    finally:
        db.commit()
        db.close()


# Initialize the database
def init_db():
    with get_db() as db:
        db.execute(
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
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """
        )
        db.execute(
            """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            file_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )"""
        )
        db.commit()


def generate_token(file_id: int):
    token = secrets.token_urlsafe(16)
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXP_MINUTES)

    with get_db() as conn:
        conn.execute(
            """
        INSERT INTO tokens (token, file_id, expires_at)
        VALUES (?, ?, ?)
        """,
            (token, file_id, expires_at),
        )

    return token

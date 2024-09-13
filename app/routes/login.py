from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.dependencies.db import get_db
from app.dependencies.auth import pwd_context
from app.dependencies.models import LoginData

import sqlite3
import secrets

router = APIRouter()


# Routes
@router.post("/login")
async def login(
    login_data: LoginData,
    db: sqlite3.Connection = Depends(get_db),
):

    with db as conn:
        cursor = conn.execute(
            """SELECT
            u.username,
            u.password,
            k.key
            FROM users u
            JOIN keys k ON u.id = k.user_id
            WHERE u.username = ?
            """,
            (login_data.username,),
        )
        user = cursor.fetchone()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not pwd_context.verify(login_data.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"username": user[0], "password": login_data.password, "apikey": user[2]}


@router.post("/register")
async def register(user_data: LoginData, db: sqlite3.Connection = Depends(get_db)):

    with db as conn:
        cursor = conn.execute("SELECT username FROM users")
        users = cursor.fetchall()
        if any(user_data.username in values for values in users):
            raise HTTPException(status_code=400, detail="Username already exists")
        password = pwd_context.hash(user_data.password)

        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user_data.username, password),
        )
        cur = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (user_data.username,),
        )

        # generate key for general use
        id = cur.fetchone()
        key = secrets.token_urlsafe(16)
        conn.execute(
            "INSERT INTO keys (user_id, key, is_login) VALUES (?, ?, ?)",
            (id[0], key, "Y"),
        )

        return {"message": "User registered successfully"}

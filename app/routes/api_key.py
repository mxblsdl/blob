from fastapi import Depends, APIRouter

from app.dependencies.db import get_db
from app.dependencies.auth import get_api_key

import sqlite3
import secrets

router = APIRouter()


@router.post("/generate-api-key")
async def generate_api_key(
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    new_key = secrets.token_urlsafe(16)

    # return apikey
    with db as conn:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO keys (user_id, key, is_login) VALUES (?, ?, ?)",
            (user_id, new_key, "N"),
        )
        conn.commit()

    return new_key


@router.get("/get-api-key")
async def get_api_keys(
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    n = 15
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
            k.id, 
            k.key
            FROM users u
            JOIN keys k ON ? = k.user_id
            AND is_login = 'N'
            """,
            (user_id,),
        )
        result = cursor.fetchall()
    keys = [
        {
            "id": r["id"],
            "key": "*" * n + r["key"][n:],
        }
        for r in result
    ]

    return {"keys": keys}


@router.get("/delete-api-key/{id}", dependencies=[Depends(get_api_key)])
async def delete_api_key(
    id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM keys
            WHERE id = ?
            AND is_login = 'N'
            """,
            (id,),
        )
        conn.commit()
    return {"message": "success"}

from fastapi import Depends, APIRouter, Request, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies.db import get_db
from app.dependencies.auth import get_api_key

import sqlite3
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/keys/create", response_class=HTMLResponse)
async def create_api_key(
    request: Request,
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    new_key = secrets.token_urlsafe(16)

    with db as conn:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO keys (user_id, key, is_login) VALUES (?, ?, ?)",
            (user_id, new_key, "N"),
        )
        conn.commit()

    return templates.TemplateResponse(
        "new_key.html",
        {"request": request, "key": new_key},
    )


@router.get("/keys/get", response_class=HTMLResponse)
async def get_api_keys(
    request: Request,
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    # Number of characters to blank out
    n = 15
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
            k.id, 
            k.key
            FROM users u
            JOIN keys k ON u.id = k.user_id
            WHERE u.id = ?
            AND k.is_login = 'N'
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

    return templates.TemplateResponse(
        "key_table.html",
        {"request": request, "keys": keys},
    )


@router.delete("/keys/delete")
async def delete_api_key(
    key_id: str = Query(...),
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM keys
            WHERE id = ?
            AND is_login = 'N'
            AND user_id = ?
            """,
            (key_id, user_id),
        )
        conn.commit()

    headers = {"HX-Trigger": "manageKeys"}
    return Response(status_code=204, headers=headers)

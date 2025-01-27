from fastapi import APIRouter, Depends, Request, Form

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies.db import get_db
from app.dependencies.auth import pwd_context
import sqlite3
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Routes
@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.execute(
            """SELECT
            u.id,
            u.username,
            u.password,
            k.key
            FROM users u
            JOIN keys k ON u.id = k.user_id
            WHERE u.username = ?
            """,
            (username,),
        )
        try:
            id, user, user_password, key = cursor.fetchone()
        except Exception as e:
            print(e)
            return HTMLResponse(
                content="", status_code=404, headers={"HX-Trigger": "user-not-found"}
            )

    if not pwd_context.verify(password, user_password):
        return HTMLResponse(
            content="", status_code=404, headers={"HX-Trigger": "password-incorrect"}
        )
    folder_id = check_root(id, db)

    # So the response sends the folder_id and the user_id and maybe the api key
    return templates.TemplateResponse(
        "dropbox.html",
        context={
            "request": request,
            "username": username,
            "key": key,
            "folder_id": folder_id,
        },
    )


def check_root(
    user_id: int,
    db: sqlite3.Connection,
):
    with db as conn:
        cursor = conn.execute(
            """SELECT id 
                    FROM folders 
                    WHERE user_id = ?
                    AND parent_folder_id IS NULL""",
            (user_id,),
        )
        res = cursor.fetchone()

        if not res:
            cursor = conn.execute(
                """INSERT INTO folders 
                    (user_id, parent_folder_id, folder_name) VALUES (?, NULL, 'root')
                    """,
                (user_id,),
            )
            id = cursor.lastrowid
        else:
            id = res[0]
        return id


def check_existing_user(
    username: str, password: str, db: sqlite3.Connection
) -> int | None:
    with db as conn:
        cursor = conn.execute("SELECT username FROM users")
        users = cursor.fetchall()
        if any(username in values for values in users):
            return None
        password = pwd_context.hash(password)

        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )
        cur = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        )
        id = cur.fetchone()
        key = secrets.token_urlsafe(16)
        conn.execute(
            "INSERT INTO keys (user_id, key, is_login) VALUES (?, ?, ?)",
            (id[0], key, "Y"),
        )
        return 1


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db),
):
    result = check_existing_user(username, password, db)
    print(result)
    if result:
        return templates.TemplateResponse(
            "alert.html",
            {
                "request": request,
                "message": "User registered successfully",
                "type": "success",
            },
        )

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "message": "Registration failed: User already exists",
            "type": "error",
        },
    )


@router.get("/show_register", response_class=HTMLResponse)
async def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

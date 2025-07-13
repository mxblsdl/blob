from fastapi import APIRouter, Depends, Request, Form, Cookie

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies.db import get_db
from app.dependencies.auth import pwd_context
import sqlite3
import secrets
from jose import jwt, JWTError
from datetime import datetime
from typing import Optional
from datetime import timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# JWT Token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Routes
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db),
    redirect_to: str = Form("/"),
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
    
    # check if the user has a root folder
    folder_id = check_root(id, db)


    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user},
        expires_delta=access_token_expires,
    )

    response = RedirectResponse(url=redirect_to, status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=True,  # Only send over HTTPS in production
        samesite="lax",  # CSRF protection
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Cookie expiry in seconds
    )

    return response


    # So the response sends the folder_id and the user_id and maybe the api key
    return templates.TemplateResponse(
        "index.html",
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


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request, current_user: str | None = None
):  # TODO replace with get_current_user
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request})


# Configuration
# TODO move into a config file
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_current_user(token: Optional[str] = Cookie(None, alias="access_token")):
    """Dependency to get current user from JWT token in cookie"""
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None

        # Check if token is expired (jose handles this automatically, but you can add custom logic)
        exp = payload.get("exp")
        if exp and datetime.now().timestamp() > exp:
            return None

    except JWTError:
        return None

    # user = get_user(username)
    return username

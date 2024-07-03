from fastapi import APIRouter, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from fastapi.exceptions import HTTPException

from app.dependencies.db import get_db, generate_token
from app.auth import pwd_context, get_api_key

import sqlite3
from datetime import datetime
from pydantic import BaseModel
import secrets
import io


class LoginData(BaseModel):
    username: str
    password: str


router = APIRouter()


# Routes
@router.post("/login")
async def login(login_data: LoginData, db: sqlite3.Connection = Depends(get_db)):

    with db as conn:
        cursor = conn.execute(
            """SELECT
            u.username,
            u.password,
            k.key
            FROM users u
            JOIN keys k ON u.id = k.key_id
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
        conn.execute("INSERT INTO keys (key_id, key) VALUES (?, ?)", (id[0], key))

        return {"message": "User registered successfully"}


# Upload functionality
@router.post("/upload")
async def upload_file(
    username=Depends(get_api_key),
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):
    print(username)
    try:
        cursor = db.cursor()
        file_contents = await file.read()
        size = len(file_contents)
        created_at = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        cursor.execute(
            """INSERT OR REPLACE INTO 
            data (file_name, user, bin, size, created_at) VALUES (?, ?, ?, ?, ?)""",
            (file.filename, username, file_contents, size, created_at),
        )
        db.commit()

        id = cursor.lastrowid
        return {"file_id": id, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def get_files(
    username: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.execute(
            "SELECT id, file_name, size, created_at FROM data WHERE user = ?",
            (username,),
        )
        rows = cursor.fetchall()
        files = [
            {
                "id": row[0],
                "filename": row[1],
                "size": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]
    return {"files": files}


@router.get("/user/files/{file_id}", dependencies=[Depends(get_api_key)])
async def get_file(
    file_id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.execute(
            "SELECT file_name, bin FROM data WHERE id = ?",
            (file_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="File not found")

        filename, content = row

        return StreamingResponse(
            content=io.BytesIO(content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.delete("/user/files/remove/{file_id}", dependencies=[Depends(get_api_key)])
async def remove_file(
    file_id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        conn.execute(
            "DELETE FROM data WHERE id = ?",
            (file_id,),
        )
        conn.commit()
        return {"message": "File Deleted"}


@router.post("/generateLink/{file_id}", dependencies=[Depends(get_api_key)])
async def generate_link(
    request: Request,
    file_id: int,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cur = conn.execute("SELECT id FROM data WHERE id = ?", (file_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="File not found")

    # Generate a unique token
    token = generate_token(file_id)
    link = f"{request.base_url}files/share/{token}"

    return {"link": link}


@router.get("/files/share/{token}")
async def get_file_by_token(
    token: str,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        SELECT d.file_name, d.bin, t.expires_at
        FROM data d
        JOIN tokens t ON d.id = t.file_id
        WHERE t.token = ?
        """,
            (token,),
        )
        result = cursor.fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    filename, content, expires_at = result

    if datetime.now() > datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S.%f"):
        raise HTTPException(status_code=403, detail="Token expired")

    return StreamingResponse(
        content=io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Request,
    Depends,
    Response,
    Security,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from fastapi.security.api_key import APIKeyHeader

import sqlite3
from datetime import datetime
import secrets
import io

from models import LoginData
from db import init_db, get_db, generate_token

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# TODO add dockerfile

# API Key dependency
api_key_header = APIKeyHeader(name="access_token", auto_error=True)


async def get_api_key(
    api_key_header: str = Security(api_key_header),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    cur.execute("SELECT * FROM keys WHERE key = ?", (api_key_header,))
    key_record = cur.fetchone()

    if key_record is None:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )

    return key_record["key"]


# Initialize app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    init_db()


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

# Routes
@app.post("/login")
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


@app.post("/register")
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
@app.post("/upload/{username}", dependencies=[Depends(get_api_key)])
async def upload_file(
    username: str,
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):

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


@app.get("/files/{username}", dependencies=[Depends(get_api_key)])
async def get_files(
    username: str,
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


@app.get("/user/files/{file_id}", dependencies=[Depends(get_api_key)])
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


@app.delete("/user/files/remove/{file_id}", dependencies=[Depends(get_api_key)])
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


@app.post("/generateLink/{file_id}", dependencies=[Depends(get_api_key)])
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


@app.get("/files/share/{token}")
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

    return Response(
        content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


app.mount("/", StaticFiles(directory="static", html=True), name="static")

from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext

import aiosqlite
from datetime import datetime

from models import LoginData
from db import init_db, init_user_db, get_db

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


# TODO add dockerfile
# TODO create shareable link to file


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_user_db()
    yield


# Initialize app with running lifespan function on start up
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

@app.post("/login")
async def login(login_data: LoginData, db: aiosqlite.Connection = Depends(get_db)):

    cursor = await db.execute(
        "SELECT * FROM users WHERE username = ?", (login_data.username,)
    )
    user = await cursor.fetchone()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not pwd_context.verify(login_data.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"username": login_data.username, "password": login_data.password}


@app.post("/register")
async def register(user_data: LoginData, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT username FROM users")
    users = await cursor.fetchall()
    if any(user_data.username in values for values in users):
        raise HTTPException(status_code=400, detail="Username already exists")
    password = pwd_context.hash(user_data.password)

    await db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (user_data.username, password),
    )
    await db.commit()

    return {"message": "User registered successfully"}


# Upload functionality
@app.post("/upload/{username}")
async def upload_file(
    username: str,
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    try:
        file_contents = await file.read()
        size = len(file_contents)
        time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        # TODO add size to database
        # TODO add date modified to database
        await db.execute(
            """INSERT OR REPLACE INTO 
            data (id, bin, user, size, date) VALUES (?, ?, ?, ?, ?)""",
            (file.filename, file_contents, username, size, time),
        )
        await db.commit()
        return {"filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{username}")
async def get_files(
    username: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT id, size, date FROM data WHERE user = ?", (username,)
    )
    rows = await cursor.fetchall()
    files = [
        {
            "filename": row[0],
            "size": row[1],
            "created_at": row[2],
        }
        for row in rows
    ]
    return {"files": files}


@app.get("/user/{username}/files/{file_id}")
async def get_file(
    file_id: str,
    username: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT id, bin FROM data WHERE id = ? AND user = ?", (file_id, username)
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="File not found")
    filename, content = row
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.delete("/user/{username}/files/{file_id}")
async def remove_file(
    file_id: str,
    username: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    await db.execute(
        "DELETE FROM data WHERE id = ? AND user = ?",
        (file_id, username),
    )
    await db.commit()
    return {"message": "File Deleted"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")

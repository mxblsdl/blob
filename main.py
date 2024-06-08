from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext

import aiosqlite

from models import LoginData
from db import init_db, init_user_db, get_db

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


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


@app.post("/login")
async def login(login_data: LoginData, db: aiosqlite.Connection = Depends(get_db)):

    cursor = await db.execute(
        "SELECT * FROM users WHERE username = ?", (login_data.username,)
    )
    user = await cursor.fetchone()
    print(user)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    print(user[1])
    if not pwd_context.verify(login_data.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid password")

    # TODO Adjust what user sees based on login / prefix table with username
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
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), db: aiosqlite.Connection = Depends(get_db)
):
    try:
        file_contents = await file.read()
        await db.execute(
            """
            INSERT OR REPLACE INTO data (id, bin) VALUES (?, ?)
        """,
            (file.filename, file_contents),
        )
        await db.commit()
        return {"filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
async def get_files(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT id FROM data")
    rows = await cursor.fetchall()
    filenames = [{"filename": row[0]} for row in rows]
    return {"filenames": filenames}


@app.get("/files/{file_id}")
async def get_file(file_id: str, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT id, bin FROM data WHERE id = ?", (file_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="File not found")
    filename, content = row
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.delete("/files/{file_id}")
async def remove_file(file_id: str, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute(
        "DELETE FROM data WHERE id = ?",
        (file_id,),
    )
    await db.commit()
    return {"message": "File Deleted"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")

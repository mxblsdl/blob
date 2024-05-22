from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import aiosqlite


# TODO init database wtih filename as primary key, update on conflict


# Initialize the database
async def init_db():
    async with aiosqlite.connect("file_uploads.db") as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id TEXT PRIMARY KEY,
                bin BLOB
            )
        """
        )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


async def get_db():
    db = await aiosqlite.connect("file_uploads.db")
    await db.set_trace_callback(print)
    try:
        yield db
    finally:
        await db.close()


@app.post("/upload/")
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


@app.get("/files/")
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


@app.get("/")
async def main():
    with open("./index.html", "r") as h:
        html = h.read()
    return HTMLResponse(html)

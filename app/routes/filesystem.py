from fastapi import APIRouter, Depends, UploadFile, File, Request, Query, Form
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates

from app.dependencies.db import get_db, generate_token
from app.dependencies.auth import get_api_key
from app.dependencies.models import Folder

import sqlite3
from datetime import datetime
import io


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Upload functionality
@router.post("/upload")
async def upload_file(
    request: Request,
    folder_id: str = Form(...),
    user_id: str = Depends(get_api_key),
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        try:
            file_contents = await file.read()
            size = len(file_contents)
            created_at = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

            conn.execute(
                """INSERT OR REPLACE INTO 
                files (user_id, file_name, folder_id, bin, size, created_at) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,  # user_id
                    file.filename,  # file_name
                    folder_id,  # folder _id
                    file_contents,  # bin
                    size,  # size
                    created_at,  # created_at
                ),
            )
            db.commit()
            return JSONResponse(
                status_code=200, content={"message": "File Upload Successful"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/items", response_class=HTMLResponse)
async def populate_items(
    request: Request,
    folder_id=Query(...),
    user_id=Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    files = await get_files(folder_id, user_id, db)
    folders = await get_folders(folder_id, user_id, db)

    return templates.TemplateResponse(
        "table.html",
        context={
            "request": request,
            "folders": folders,
            "files": files,
        },
    )


async def get_files(
    folder_id: int,
    user_id: str,
    db: sqlite3.Connection,
):
    with db as conn:
        cursor = conn.execute(
            """
            SELECT 
            id, 
            file_name,
            size, 
            created_at
            FROM files
            WHERE folder_id = ? 
            AND user_id = ?""",
            (folder_id, user_id),
        )
        rows = cursor.fetchall()
    files = [
        {
            "id": row[0],
            "name": row[1],
            "size": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]

    for file in files:
        if 1000 < file["size"] <= 999999:
            file["size"] = str(round(file["size"] / 1000, 1)) + "KB"
        elif file["size"] > 9999 and file["size"] < 999999999:
            file["size"] = str(round(file["size"] / 1000000, 1)) + "MB"
        else:
            file["size"] = str(file["size"]) + "bytes"

    return files


async def get_folders(
    folder_id: int,
    user_id: str,
    db: sqlite3.Connection,
):
    with db as conn:
        cursor = conn.execute(
            """
            SELECT *
            FROM folders 
            WHERE user_id = ?
            AND parent_folder_id = ?""",
            (user_id, folder_id),
        )
        rows = cursor.fetchall()
        folders = [
            {
                "id": row[0],
                "user_id": row[1],
                "parent_id": row[2],
                "name": row[3],
            }
            for row in rows
        ]

        # Check if in root
        root, parent_id = in_root(folder_id, db)
        if not root:
            folders.insert(
                0,
                {
                    "id": parent_id,
                    "user_id": user_id,
                    "parent_id": parent_id,
                    "name": "../",
                },
            )

    return folders


def in_root(folder_id: int, db: sqlite3.Connection) -> bool:
    # I want this to return a tuple with the patent id if False
    with db as conn:
        cursor = conn.execute(
            """SELECT parent_folder_id 
               FROM folders 
               WHERE id = ?""",
            (folder_id,),
        )
        res = cursor.fetchone()
        if res[0] is None:
            return (True, 0)
        return (False, res[0])


@router.post("/add_folder")
async def add_folder(
    folder: Folder,
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        conn.execute(
            """INSERT INTO folders 
            (user_id, parent_folder_id, folder_name) 
            VALUES (?, ?, ?)""",
            (user_id, folder.currentDir, folder.newDir),
        )
    return {"message": f"{folder.newDir} folder created successfully"}


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    user_id=Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.execute(
            """
            SELECT 
            file_name, 
            bin 
            FROM files 
            WHERE id = ?
            AND user_id = ?
            """,
            (file_id, user_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="File not found")

        filename, content = row

        print(file_id)

        return StreamingResponse(
            content=io.BytesIO(content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.delete("/delete", response_class=HTMLResponse)
async def delete_file(
    file_id: str = Query(...),
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        conn.execute(
            """DELETE FROM files 
            WHERE id = ?
            AND user_id = ?""",
            (file_id, user_id),
        )
        conn.commit()
    return HTMLResponse("File Deleted")


@router.post(
    "/user/files/link/{file_id}",
    dependencies=[Depends(get_api_key)],
)
async def generate_link(
    request: Request,
    file_id: int,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cur = conn.execute(
            """SELECT id 
                           FROM files 
                           WHERE id = ?""",
            (file_id,),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="File not found")

    # Generate a unique token
    token, expires_at = generate_token()

    with db as conn:
        conn.execute(
            """
        INSERT INTO tokens (token, file_id, expires_at)
        VALUES (?, ?, ?)
        """,
            (token, file_id, expires_at),
        )
        conn.commit()

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
        SELECT f.file_name, f.bin, t.expires_at
        FROM files f
        JOIN tokens t ON f.id = t.file_id
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


@router.get("/filepath", response_class=HTMLResponse)
async def create_file_path(
    folder_id: int = Query(...),
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cur = conn.execute(
            """
        WITH RECURSIVE directory_path(id, folder_name, path) AS (
            SELECT id, folder_name, folder_name AS path 
            FROM folders 
            WHERE parent_folder_id IS NULL AND user_id = :user -- root directory by user 1
            UNION ALL
            SELECT d.id, d.folder_name, dp.path || '/' || d.folder_name
            FROM folders d
            JOIN directory_path dp ON dp.id = d.parent_folder_id
            WHERE d.user_id = :user
        )
        SELECT * FROM directory_path
        WHERE id = :folder;
        """,
            {
                "user": user_id,
                "folder": folder_id,
            },
        )
        filepath = cur.fetchone()

        return filepath[2]

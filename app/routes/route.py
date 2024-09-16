from fastapi import APIRouter, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from fastapi.exceptions import HTTPException

from app.dependencies.db import get_db, generate_token
from app.dependencies.auth import get_api_key
from app.dependencies.models import Folder, FolderId

import sqlite3
from datetime import datetime
import io


router = APIRouter()


# Upload functionality
@router.post("/upload/{current_dir}")
async def upload_file(
    current_dir: str,
    user_id=Depends(get_api_key),
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        try:
            file_contents = await file.read()
            size = len(file_contents)
            created_at = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

            cursor = conn.execute(
                """INSERT OR REPLACE INTO 
                files (user_id, file_name, folder_id, bin, size, created_at) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,  # user_id
                    file.filename,  # file_name
                    current_dir,  # folder _id
                    file_contents,  # bin
                    size,  # size
                    created_at,  # created_at
                ),
            )
            db.commit()

            id = cursor.lastrowid
            return {"file_id": id, "filename": file.filename}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/files")
async def get_files(
    folderId: FolderId,
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
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
            (folderId.id, user_id),
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
    return {"files": files}


@router.post("/folders")
async def get_folders(
    folderId: FolderId,
    user_id: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.execute(
            """
            SELECT *
            FROM folders 
            WHERE user_id = ?
            AND parent_folder_id = ?""",
            (user_id, folderId.id),
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
        root, parent_id = in_root(folderId.id, db)
        if not root:
            folders.insert(0,
                {
                    "id": parent_id,
                    "user_id": user_id,
                    "parent_id": parent_id,
                    "name": "../",
                }
            )

    return {"folders": folders, "current_folder": folderId.id}


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


@router.get(
    "/user/files/{file_id}",
    dependencies=[Depends(get_api_key)],
)
async def download_file(
    file_id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        cursor = conn.execute(
            """
            SELECT 
            file_name, 
            bin 
            FROM files 
            WHERE id = ?""",
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


@router.delete(
    "/user/files/remove/{file_id}",
    dependencies=[Depends(get_api_key)],
)
async def delete_file(
    file_id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    with db as conn:
        conn.execute(
            """DELETE FROM files 
            WHERE id = ?""",
            (file_id,),
        )
        conn.commit()
        return {"message": "File Deleted"}


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



@router.get("/filepath/{folder_id}")
async def create_file_path(
    folder_id: int,
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

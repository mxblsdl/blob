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
    print(folderId)
    if not folderId.id:
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
                folderId.id = cursor.lastrowid
            else:
                folderId.id = res[0]

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
                "user_id": row[2],
                "parent_id": row[3],
                "name": row[4],
            }
            for row in rows
        ]
    return {"folders": folders, "current_folder": folderId.id}


@router.post("/add_folder")
async def add_folder(
    folder: Folder,
    username: str = Depends(get_api_key),
    db: sqlite3.Connection = Depends(get_db),
):
    print(folder)
    with db as conn:
        conn.execute(
            "INSERT INTO folders (name, parent, user) VALUES (?, ?, ?)",
            (folder.new_dir, folder.current_dir, username),
        )
    return {"message": f"{folder.new_dir} folder created successfully"}


@router.get(
    "/user/files/{file_id}",
    dependencies=[Depends(get_api_key)],
)
async def get_file(
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
async def remove_file(
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
    print(token)
    print(expires_at)

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


# TODO the following is a set of SQL that can be used to populate the file path
# WITH RECURSIVE directory_path(id, name, path) AS (
#     SELECT id, name, name AS path FROM directories WHERE id = 1 AND user_id = 1 -- root directory by user 1
#     UNION ALL
#     SELECT d.id, d.name, dp.path || '/' || d.name
#     FROM directories d
#     JOIN directory_path dp ON dp.id = d.parent_id
#     WHERE d.user_id = 1
# )
# SELECT * FROM directory_path;

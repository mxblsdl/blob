from fastapi import Security, Depends
from fastapi.exceptions import HTTPException
from fastapi.security.api_key import APIKeyHeader

from passlib.context import CryptContext
import sqlite3

from app.dependencies.db import get_db

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# API Key dependency
api_key_header = APIKeyHeader(name="access_token", auto_error=False)


async def get_api_key(
    api_key_header: str = Security(api_key_header),
    db: sqlite3.Connection = Depends(get_db),
) -> str:
    if not api_key_header:
        raise HTTPException(
            status_code=403,
            detail="API key is missing. Please provide an API key.",
        )

    cur = db.cursor()
    cur.execute(
        """SELECT u.id
            FROM users u
            JOIN keys k ON u.id = k.user_id
            WHERE k.key = ?""",
        (api_key_header,),
    )
    key_record = cur.fetchone()

    if key_record is None:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Please provide a valid API key.",
        )

    return key_record["id"]

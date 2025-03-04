import pytest
from fastapi.testclient import TestClient
from app.routes.filesystem import router
from app.dependencies.db import get_db
from app.dependencies.auth import get_api_key
from fastapi import FastAPI
import sqlite3

app = FastAPI()
app.include_router(router)

client = TestClient(app)


# Mock dependencies
def override_get_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            file_name TEXT,
            folder_id TEXT,
            bin BLOB,
            size INTEGER,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE folders (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            parent_folder_id INTEGER,
            folder_name TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE tokens (
            token TEXT PRIMARY KEY,
            file_id INTEGER,
            expires_at TEXT
        )
        """
    )
    return conn


def override_get_api_key():
    return "test_user"


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_api_key] = override_get_api_key


@pytest.fixture
def db():
    return override_get_db()


def test_upload_file(db):
    response = client.post(
        "/upload",
        data={"folder_id": "1"},
        files={"file": ("test.txt", b"test content")},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "File Upload Successful"}


def test_populate_items(db):
    response = client.get("/items", params={"folder_id": 1})
    assert response.status_code == 200
    assert "folders" in response.text
    assert "files" in response.text


def test_download_file(db):
    db.execute(
        """
        INSERT INTO files (user_id, file_name, folder_id, bin, size, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("test_user", "test.txt", "1", b"test content", 12, "2023/01/01 00:00:00"),
    )
    db.commit()
    response = client.get("/download/1")
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=test.txt"


def test_delete_file(db):
    db.execute(
        """
        INSERT INTO files (user_id, file_name, folder_id, bin, size, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("test_user", "test.txt", "1", b"test content", 12, "2023/01/01 00:00:00"),
    )
    db.commit()
    response = client.delete("/delete/file", params={"file_id": 1})
    assert response.status_code == 200
    assert "Object deleted" in response.text


def test_create_folder(db):
    response = client.post(
        "/folder/create",
        data={"folder_id": "1", "folder_name": "new_folder"},
    )
    assert response.status_code == 200
    assert "Folder created" in response.text


def test_delete_folder(db):
    db.execute(
        """
        INSERT INTO folders (user_id, parent_folder_id, folder_name)
        VALUES (?, ?, ?)
        """,
        ("test_user", None, "root_folder"),
    )
    db.commit()
    response = client.delete("/folder/delete", params={"folder_id": 1})
    assert response.status_code == 200
    assert "Folder deleted" in response.text


def test_create_link(db):
    db.execute(
        """
        INSERT INTO files (user_id, file_name, folder_id, bin, size, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("test_user", "test.txt", "1", b"test content", 12, "2023/01/01 00:00:00"),
    )
    db.commit()
    response = client.post(
        "/files/share",
        data={"file_id": "1"},
    )
    assert response.status_code == 200
    assert "link" in response.json()


def test_get_file_by_token(db):
    db.execute(
        """
        INSERT INTO files (user_id, file_name, folder_id, bin, size, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("test_user", "test.txt", "1", b"test content", 12, "2023/01/01 00:00:00"),
    )
    db.execute(
        """
        INSERT INTO tokens (token, file_id, expires_at)
        VALUES (?, ?, ?)
        """,
        ("test_token", 1, "2099-01-01 00:00:00.000000"),
    )
    db.commit()
    response = client.get("/files/share/test_token")
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=test.txt"


def test_create_file_path(db):
    db.execute(
        """
        INSERT INTO folders (user_id, parent_folder_id, folder_name)
        VALUES (?, ?, ?)
        """,
        ("test_user", None, "root_folder"),
    )
    db.commit()
    response = client.get("/filepath", params={"folder_id": 1})
    assert response.status_code == 200
    assert response.text == "root_folder"

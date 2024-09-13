from pydantic import BaseModel


class LoginData(BaseModel):
    username: str
    password: str


class Folder(BaseModel):
    current_dir: str
    new_dir: str | None


class FolderId(BaseModel):
    id: int | None = None

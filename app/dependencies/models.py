from pydantic import BaseModel


# class LoginData(BaseModel):
#     username: str
#     password: str


class Folder(BaseModel):
    currentDir: str
    newDir: str | None


class FolderId(BaseModel):
    id: int

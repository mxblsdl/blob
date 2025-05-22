from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes import filesystem, login, api_key
from app.dependencies.db import init_db
from contextlib import asynccontextmanager


# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    init_db()
    yield
    # Code to run on shutdown
    # (if needed, e.g., closing database connections)
    pass


# Initialize app
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(filesystem.router)
app.include_router(login.router)
app.include_router(api_key.router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

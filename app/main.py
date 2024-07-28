from fastapi import (
    FastAPI,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes import route
from app.dependencies.db import init_db

# TODO add dockerfile
# TODO button to generate API key for user
# Should also delete API keys or view hashed keys

# Initialize app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    init_db()


app.include_router(route.router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

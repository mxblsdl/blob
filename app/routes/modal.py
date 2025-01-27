from fastapi import (
    APIRouter,
    Request,
    Query,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/modal/create", response_class=HTMLResponse)
async def create_modal(
    request: Request,
    folder_id: str = Query(...),
):
    return templates.TemplateResponse(
        "folder_modal.html",
        {"request": request, "folder_id": folder_id},
    )


@router.get("/modal/close", response_class=HTMLResponse)
async def close_modal():
    return HTMLResponse("")

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import link as link_service

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
async def redirect(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    link = await link_service.redirect_link(db, short_code)

    background_tasks.add_task(
        link_service.log_click, link.id, ip_address, user_agent, referer
    )

    return RedirectResponse(link.original_url, status_code=307)

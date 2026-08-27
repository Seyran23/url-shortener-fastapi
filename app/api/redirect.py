
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import link as link_service

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
async def redirect(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:  
    original_url = await link_service.redirect_link(db, short_code)

    return RedirectResponse(original_url, status_code=307)

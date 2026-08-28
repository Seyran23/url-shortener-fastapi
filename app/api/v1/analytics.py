from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.constants import LINKS_PREFIX
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsSummary,
    BrowserBreakdown,
    CountryBreakdown,
    DeviceBreakdown,
    ReferrerBreakdown,
    TimeseriesPoint,
)
from app.services import analytics as analytics_service

router = APIRouter(prefix=f"{LINKS_PREFIX}/{{link_id}}/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_summary(db, link_id, current_user.id)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
async def get_timeseries(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_timeseries(db, link_id, current_user.id)


@router.get("/countries", response_model=list[CountryBreakdown])
async def get_by_country(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_by_country(db, link_id, current_user.id)


@router.get("/devices", response_model=list[DeviceBreakdown])
async def get_by_device(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_by_device(db, link_id, current_user.id)


@router.get("/browsers", response_model=list[BrowserBreakdown])
async def get_by_browser(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_by_browser(db, link_id, current_user.id)


@router.get("/referrers", response_model=list[ReferrerBreakdown])
async def get_by_referrer(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_by_referrer(db, link_id, current_user.id)

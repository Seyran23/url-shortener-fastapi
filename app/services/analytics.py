from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import analytics as analytics_repo
from app.services import link as link_service


async def get_summary(db: AsyncSession, link_id: UUID, user_id: UUID) -> dict:
    await link_service.get_owned(db, link_id, user_id)
    return await analytics_repo.get_summary(db, link_id)


async def get_timeseries(db: AsyncSession, link_id: UUID, user_id: UUID) -> list[dict]:
    await link_service.get_owned(db, link_id, user_id)
    return await analytics_repo.get_timeseries(db, link_id)


async def get_by_country(db: AsyncSession, link_id: UUID, user_id: UUID) -> list[dict]:
    await link_service.get_owned(db, link_id, user_id)
    return await analytics_repo.get_by_country(db, link_id)


async def get_by_device(db: AsyncSession, link_id: UUID, user_id: UUID) -> list[dict]:
    await link_service.get_owned(db, link_id, user_id)
    return await analytics_repo.get_by_device(db, link_id)


async def get_by_browser(db: AsyncSession, link_id: UUID, user_id: UUID) -> list[dict]:
    await link_service.get_owned(db, link_id, user_id)
    return await analytics_repo.get_by_browser(db, link_id)


async def get_by_referrer(db: AsyncSession, link_id: UUID, user_id: UUID) -> list[dict]:
    await link_service.get_owned(db, link_id, user_id)
    return await analytics_repo.get_by_referrer(db, link_id)

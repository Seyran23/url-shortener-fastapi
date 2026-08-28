from datetime import datetime, timedelta, timezone
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


async def get_owner_summary(db: AsyncSession, user_id: UUID) -> dict:
    return await analytics_repo.get_owner_summary(db, user_id)


async def get_owner_clicks_today(db: AsyncSession, user_id: UUID) -> int:
    since = datetime.now(timezone.utc) - timedelta(days=1)
    return await analytics_repo.get_owner_clicks_since(db, user_id, since)


async def get_owner_clicks_this_week(db: AsyncSession, user_id: UUID) -> int:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    return await analytics_repo.get_owner_clicks_since(db, user_id, since)


async def get_owner_top_links(db: AsyncSession, user_id: UUID, limit: int = 5) -> list[dict]:
    return await analytics_repo.get_owner_top_links(db, user_id, limit)


async def get_owner_top_links_today(
    db: AsyncSession, user_id: UUID, limit: int = 5
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=1)
    return await analytics_repo.get_owner_top_links_since(db, user_id, since, limit)


async def get_owner_top_links_this_week(
    db: AsyncSession, user_id: UUID, limit: int = 5
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    return await analytics_repo.get_owner_top_links_since(db, user_id, since, limit)


async def get_owner_by_country(db: AsyncSession, user_id: UUID, limit: int = 5) -> list[dict]:
    return await analytics_repo.get_owner_by_country(db, user_id, limit)


async def get_owner_by_device(db: AsyncSession, user_id: UUID, limit: int = 5) -> list[dict]:
    return await analytics_repo.get_owner_by_device(db, user_id, limit)


async def get_owner_by_browser(db: AsyncSession, user_id: UUID, limit: int = 5) -> list[dict]:
    return await analytics_repo.get_owner_by_browser(db, user_id, limit)


async def get_owner_by_referrer(db: AsyncSession, user_id: UUID, limit: int = 5) -> list[dict]:
    return await analytics_repo.get_owner_by_referrer(db, user_id, limit)

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Analytics


async def create_analytics(
    db: AsyncSession,
    link_id: UUID,
    visitor_hash: str,
    user_agent: str | None,
    referer: str | None,
    country: str | None,
    browser: str | None,
    os: str | None,
    device_type: str | None,
) -> Analytics:
    analytics = Analytics(
        link_id=link_id,
        visitor_hash=visitor_hash,
        user_agent=user_agent,
        referer=referer,
        country=country,
        browser=browser,
        os=os,
        device_type=device_type,
    )

    db.add(analytics)
    await db.flush()
    return analytics



async def get_summary(db: AsyncSession, link_id: UUID) -> dict:
    total_clicks = await db.scalar(
        select(func.count(Analytics.id)).where(Analytics.link_id == link_id)
    )
    unique_visitors = await db.scalar(
        select(func.count(func.distinct(Analytics.visitor_hash))).where(
            Analytics.link_id == link_id
        )
    )
    return {"total_clicks": total_clicks, "unique_visitors": unique_visitors}


async def get_timeseries(db: AsyncSession, link_id: UUID) -> list[dict]:
    timeseries = await db.execute(
        select(
            func.date_trunc("day", Analytics.clicked_at).label("date"),
            func.count(Analytics.id).label("count"),
        )
        .where(Analytics.link_id == link_id)
        .group_by("date")
        .order_by("date")
    )
    return [{"date": row.date, "count": row.count} for row in timeseries.fetchall()]

async def get_by_country(db: AsyncSession, link_id: UUID) -> list[dict]:
    country_data = await db.execute(
        select(
            Analytics.country.label("country"),
            func.count(Analytics.id).label("count"),
        )
        .where(Analytics.link_id == link_id)
        .group_by(Analytics.country)
    )
    return [{"country": row.country, "count": row.count} for row in country_data.fetchall()]

async def get_by_device(db: AsyncSession, link_id: UUID) -> list[dict]:
    device_data = await db.execute(
        select(
            Analytics.device_type.label("device_type"),
            func.count(Analytics.id).label("count"),
        )
        .where(Analytics.link_id == link_id)
        .group_by(Analytics.device_type)
    )
    return [{"device_type": row.device_type, "count": row.count} for row in device_data.fetchall()]

async def get_by_browser(db: AsyncSession, link_id: UUID) -> list[dict]:
    browser_data = await db.execute(
        select(
            Analytics.browser.label("browser"),
            func.count(Analytics.id).label("count"),
        )
        .where(Analytics.link_id == link_id)
        .group_by(Analytics.browser)
    )
    return [{"browser": row.browser, "count": row.count} for row in browser_data.fetchall()]

async def get_by_referrer(db: AsyncSession, link_id: UUID) -> list[dict]:   
    referrer_data = await db.execute(
        select(
            Analytics.referer.label("referer"),
            func.count(Analytics.id).label("count"),
        )
        .where(Analytics.link_id == link_id)
        .group_by(Analytics.referer)
    )
    return [{"referer": row.referer, "count": row.count} for row in referrer_data.fetchall()]

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Analytics


async def create_analytics(
    db: AsyncSession,
    link_id: UUID,
    visitor_hash: str,
    user_agent: str | None,
    referer: str | None,
    country: str | None,
) -> Analytics:
    analytics = Analytics(
        link_id=link_id,
        visitor_hash=visitor_hash,
        user_agent=user_agent,
        referer=referer,
        country=country,
    )

    db.add(analytics)
    await db.flush()
    return analytics
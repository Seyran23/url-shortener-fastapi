from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import CursorResult, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link


async def create(
    db: AsyncSession,
    user_id: UUID,
    short_code: str,
    original_url: str,
    expires_at: datetime | None,
    max_clicks: int | None,
) -> Link:
    new_link = Link(
        user_id=user_id,
        short_code=short_code,
        original_url=str(original_url),
        expires_at=expires_at,
        max_clicks=max_clicks,
    )

    db.add(new_link)
    await db.flush()
    await db.refresh(new_link)

    return new_link


async def get_by_short_code(db: AsyncSession, short_code: str) -> Link | None:
    link = await db.execute(select(Link).where(Link.short_code == short_code))

    return link.scalar_one_or_none()


async def get_owned(db: AsyncSession, link_id: UUID, user_id: UUID) -> Link | None:
    link = await db.execute(
        select(Link).where(Link.id == link_id, Link.user_id == user_id)
    )

    return link.scalar_one_or_none()


async def list_for_owner(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
) -> list[Link]:
    links = await db.execute(
        select(Link).where(Link.user_id == user_id).offset(skip).limit(limit)
    )

    return list(links.scalars().all())


async def update_link(db: AsyncSession, link: Link, **fields) -> Link | None:
    statement = update(Link).where(Link.id == link.id).values(**fields)
    result = cast(CursorResult, await db.execute(statement))

    if result.rowcount == 0:
        return None

    await db.flush()
    await db.refresh(link)

    return link


async def increment_click_count(db: AsyncSession, link: Link) -> Link:
    statement = (
        update(Link).where(Link.id == link.id).values(click_count=Link.click_count + 1)
    )

    await db.execute(statement)
    await db.flush()
    await db.refresh(link)

    return link


async def delete(db: AsyncSession, link: Link) -> None:
    await db.delete(link)
    await db.flush()

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AliasAlreadyExistsError,
    AppError,
    ClickLimitReachedError,
    LinkExpiredError,
    LinkNotActiveError,
    LinkNotFoundError,
    LinkUnavailableError,
)
from app.core.geo import resolve_country
from app.core.helpers.hashing import hash_visitor
from app.core.helpers.short_code import generate_short_code
from app.db.session import SessionLocal
from app.models.link import Link
from app.repositories import analytics as analytics_repo
from app.repositories import links as link_repo
from app.schemas.links import LinkCreate

logger = logging.getLogger(__name__)

MAX_GENERATION_ATTEMPTS = 3

async def create(db: AsyncSession, user_id: UUID, link_data: LinkCreate) -> Link:
    if link_data.custom_alias is not None:
        try:
            link = await link_repo.create(
                db,
                user_id,
                link_data.custom_alias,
                str(link_data.original_url),
                link_data.expires_at,
                link_data.max_clicks,
            )
            await db.commit()
            logger.info(
                "Link created: short_code=%s owner=%s custom_alias=True", link.short_code, user_id
            )
            return link
        except IntegrityError:
            await db.rollback()
            raise AliasAlreadyExistsError()

    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            link = await link_repo.create(
                db,
                user_id,
                generate_short_code(),
                str(link_data.original_url),
                link_data.expires_at,
                link_data.max_clicks,
            )
            await db.commit()
            logger.info(
                "Link created: short_code=%s owner=%s custom_alias=False", link.short_code, user_id
            )
            return link
        except IntegrityError:
            await db.rollback()
            logger.warning(
                "Generated short code collided, retrying: attempt=%d/%d",
                attempt,
                MAX_GENERATION_ATTEMPTS,
            )

    logger.error("Exhausted %d attempts generating a unique short code", MAX_GENERATION_ATTEMPTS)
    raise AppError("Could not generate a unique short code, please try again")


async def redirect_link(db: AsyncSession, short_code: str) -> Link:
    link = await link_repo.get_by_short_code(db, short_code)

    if link is None:
        raise LinkNotFoundError()

    if not link.is_active:
        raise LinkNotActiveError()

    if link.expires_at is not None and link.expires_at <= datetime.now(timezone.utc):
        raise LinkUnavailableError()

    if link.max_clicks is not None and link.click_count >= link.max_clicks:
        raise LinkUnavailableError()

    await link_repo.increment_click_count(db, link)
    await db.commit()

    return link


async def log_click(
    link_id: UUID, ip_address: str, user_agent: str | None, referer: str | None
) -> None:
    async with SessionLocal() as db:
        country = resolve_country(ip_address)
        await analytics_repo.create_analytics(
            db, link_id, hash_visitor(ip_address, user_agent), user_agent, referer, country
        )
        await db.commit()


async def get_by_short_code(db: AsyncSession, short_code: str) -> Link:
    link = await link_repo.get_by_short_code(db, short_code)

    if not link:
        raise LinkNotFoundError()

    return link


async def get_owned(db: AsyncSession, link_id: UUID, user_id: UUID) -> Link:
    link = await link_repo.get_owned(db, link_id, user_id)

    if not link:
        raise LinkNotFoundError()

    return link


async def list_for_owner(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
) -> list[Link]:
    return await link_repo.list_for_owner(db, user_id, skip, limit)


async def update_link(db: AsyncSession, link: Link, **fields) -> Link:
    updated_link = await link_repo.update_link(db, link, **fields)

    if updated_link is None:
        raise LinkNotFoundError()

    await db.commit()

    logger.info("Link updated: link_id=%s fields=%s", link.id, list(fields.keys()))

    return updated_link


async def set_active(db: AsyncSession, link: Link, is_active: bool) -> Link:
    updated_link = await link_repo.update_link(db, link, is_active=is_active)

    if updated_link is None:
        raise LinkNotFoundError()

    await db.commit()

    logger.info("Link %s: link_id=%s", "activated" if is_active else "deactivated", link.id)

    return updated_link


async def activate_link(db: AsyncSession, link: Link) -> Link:
    now = datetime.now(timezone.utc)

    if link.expires_at is not None and link.expires_at <= now:
        raise LinkExpiredError()

    if link.max_clicks is not None and link.max_clicks <= link.click_count:
        raise ClickLimitReachedError()

    return await set_active(db, link, is_active=True)


async def deactivate_link(db: AsyncSession, link: Link) -> Link:
    return await set_active(db, link, is_active=False)


async def delete(db: AsyncSession, link: Link) -> None:
    link_id, short_code = link.id, link.short_code

    await link_repo.delete(db, link)
    await db.commit()

    logger.info("Link deleted: link_id=%s short_code=%s", link_id, short_code)

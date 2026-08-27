import secrets
import string
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
from app.models.link import Link
from app.repositories import links as link_repo
from app.schemas.links import LinkCreate

ALPHABET = string.ascii_letters + string.digits
MAX_GENERATION_ATTEMPTS = 3


def _generate_short_code(length: int = 8) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


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
            return link
        except IntegrityError:
            await db.rollback()
            raise AliasAlreadyExistsError()

    for _ in range(MAX_GENERATION_ATTEMPTS):
        try:
            link = await link_repo.create(
                db,
                user_id,
                _generate_short_code(),
                str(link_data.original_url),
                link_data.expires_at,
                link_data.max_clicks,
            )
            await db.commit()
            return link
        except IntegrityError:
            await db.rollback()

    raise AppError("Could not generate a unique short code, please try again")


async def redirect_link(db: AsyncSession, short_code: str) -> str:
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

    return link.original_url



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

    return updated_link


async def set_active(db: AsyncSession, link: Link, is_active: bool) -> Link:
    updated_link = await link_repo.update_link(db, link, is_active=is_active)

    if updated_link is None:
        raise LinkNotFoundError()

    await db.commit()

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
    await link_repo.delete(db, link)
    await db.commit()


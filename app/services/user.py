import logging
import secrets
from typing import cast
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    TELEGRAM_LINK_CODE_ALPHABET,
    TELEGRAM_LINK_CODE_PREFIX,
    TELEGRAM_LINK_CODE_TTL_SECONDS,
)
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidTelegramLinkCodeError,
    TelegramChatAlreadyLinkedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.redis_client import redis_client
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    existing_user = await user_repo.get_by_email(db, user_in.email)

    if existing_user:
        raise UserAlreadyExistsError()

    user = await user_repo.create(db, user_in.email, hash_password(user_in.password))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError()

    await db.refresh(user)

    logger.info("User registered: email=%s user_id=%s", user.email, user.id)

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await user_repo.get_by_email(db, email)

    if user is None:
        logger.warning("Failed login attempt: email=%s reason=no_such_user", email)
        raise InvalidCredentialsError()

    if not verify_password(password, user.hashed_password):
        logger.warning("Failed login attempt: email=%s reason=wrong_password", email)
        raise InvalidCredentialsError()

    return user


async def delete_user(db: AsyncSession, email: str) -> None:
    user = await user_repo.get_by_email(db, email)

    if user is None:
        raise UserNotFoundError()

    await db.delete(user)
    await db.commit()

    logger.info("User deleted: email=%s user_id=%s", email, user.id)


def _generate_telegram_link_code(length: int = 8) -> str:
    return "".join(secrets.choice(TELEGRAM_LINK_CODE_ALPHABET) for _ in range(length))


async def generate_telegram_link_code(user_id: UUID) -> tuple[str, int]:
    code = _generate_telegram_link_code()
    await redis_client.set(
        f"{TELEGRAM_LINK_CODE_PREFIX}{code}", str(user_id), ex=TELEGRAM_LINK_CODE_TTL_SECONDS
    )
    return code, TELEGRAM_LINK_CODE_TTL_SECONDS


async def link_telegram_chat(db: AsyncSession, code: str, chat_id: int) -> User:
    raw = await redis_client.getdel(f"{TELEGRAM_LINK_CODE_PREFIX}{code}")

    if raw is None:
        raise InvalidTelegramLinkCodeError()

    user_id = UUID(cast(str, raw))

    try:
        await user_repo.set_telegram_chat_id(db, user_id, chat_id)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise TelegramChatAlreadyLinkedError()

    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()

    logger.info("Telegram linked: user_id=%s chat_id=%s", user_id, chat_id)

    return user


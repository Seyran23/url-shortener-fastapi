import logging
from functools import wraps
from uuid import UUID

from aiogram.types import Message

from app.core.config import settings
from app.repositories import user as user_repo
from app.telegram.formatters import format_error

logger = logging.getLogger(__name__)

_owner_user_id: UUID | None = None


def is_authorized(message: Message) -> bool:
    return message.chat.id == settings.TELEGRAM_CHAT_ID


async def get_owner_id(db) -> UUID:
    global _owner_user_id
    if _owner_user_id is None:
        if settings.TELEGRAM_OWNER_EMAIL is None:
            raise RuntimeError("TELEGRAM_OWNER_EMAIL is not configured")

        user = await user_repo.get_by_email(db, settings.TELEGRAM_OWNER_EMAIL)
        if user is None:
            raise RuntimeError(
                f"No user found for TELEGRAM_OWNER_EMAIL={settings.TELEGRAM_OWNER_EMAIL}"
            )
        _owner_user_id = user.id
    return _owner_user_id


def authorized_handler(func):
    @wraps(func)
    async def wrapper(message: Message) -> None:
        if not is_authorized(message):
            logger.warning(
                "Ignored %r from unauthorized chat_id=%s", message.text, message.chat.id
            )
            return

        try:
            await func(message)
        except Exception:
            logger.exception("Failed to handle %r", message.text)
            await message.answer(format_error())

    return wrapper

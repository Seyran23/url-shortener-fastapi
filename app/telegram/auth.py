import logging
from functools import wraps
from uuid import UUID

from aiogram.types import Message

from app.db.session import SessionLocal
from app.repositories import user as user_repo
from app.telegram.formatters import format_error, format_not_linked

logger = logging.getLogger(__name__)


async def resolve_user_id(chat_id: int) -> UUID | None:
    async with SessionLocal() as db:
        user = await user_repo.get_by_telegram_chat_id(db, chat_id)
        return user.id if user else None


def authorized_handler(func):
    @wraps(func)
    async def wrapper(message: Message) -> None:
        user_id = await resolve_user_id(message.chat.id)

        if user_id is None:
            logger.warning(
                "Ignored %r from unlinked chat_id=%s", message.text, message.chat.id
            )
            await message.answer(format_not_linked())
            return

        try:
            await func(message, user_id)
        except Exception:
            logger.exception("Failed to handle %r", message.text)
            await message.answer(format_error())

    return wrapper

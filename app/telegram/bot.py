import asyncio
import logging
from uuid import UUID

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.exceptions import (
    InvalidTelegramLinkCodeError,
    TelegramChatAlreadyLinkedError,
)
from app.core.logging_config import configure_logging
from app.db.session import SessionLocal
from app.repositories import user as user_repo
from app.services import analytics as analytics_service
from app.services import user as user_service
from app.telegram.auth import authorized_handler
from app.telegram.formatters import (
    format_breakdown,
    format_help,
    format_link_already_linked,
    format_link_invalid_code,
    format_link_success,
    format_link_usage,
    format_period,
    format_stats,
    format_top,
    format_unknown_command,
)

configure_logging()
logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("link"))
async def cmd_link(message: Message, command: CommandObject) -> None:
    code = (command.args or "").strip()

    if not code:
        await message.answer(format_link_usage())
        return

    try:
        async with SessionLocal() as db:
            await user_service.link_telegram_chat(db, code, message.chat.id)
    except InvalidTelegramLinkCodeError:
        await message.answer(format_link_invalid_code())
        return
    except TelegramChatAlreadyLinkedError:
        await message.answer(format_link_already_linked())
        return

    await message.answer(format_link_success())


@router.message(Command("start"))
@authorized_handler
async def cmd_start(message: Message, user_id: UUID) -> None:
    await message.answer("Bot is connected.")


@router.message(Command("help"))
@authorized_handler
async def cmd_help(message: Message, user_id: UUID) -> None:
    await message.answer(format_help())


@router.message(Command("stats"))
@authorized_handler
async def cmd_stats(message: Message, user_id: UUID) -> None:
    async with SessionLocal() as db:
        summary = await analytics_service.get_owner_summary(db, user_id)
        top_links = await analytics_service.get_owner_top_links(db, user_id)

    await message.answer(format_stats(summary, top_links))


@router.message(Command("today"))
@authorized_handler
async def cmd_today(message: Message, user_id: UUID) -> None:
    async with SessionLocal() as db:
        count = await analytics_service.get_owner_clicks_today(db, user_id)
        top_links = await analytics_service.get_owner_top_links_today(db, user_id)

    await message.answer(format_period("Today", count, top_links))


@router.message(Command("week"))
@authorized_handler
async def cmd_week(message: Message, user_id: UUID) -> None:
    async with SessionLocal() as db:
        count = await analytics_service.get_owner_clicks_this_week(db, user_id)
        top_links = await analytics_service.get_owner_top_links_this_week(db, user_id)

    await message.answer(format_period("This Week", count, top_links))


@router.message(Command("top"))
@authorized_handler
async def cmd_top(message: Message, user_id: UUID) -> None:
    async with SessionLocal() as db:
        top_links = await analytics_service.get_owner_top_links(db, user_id)

    await message.answer(format_top(top_links))


@router.message(Command("breakdown"))
@authorized_handler
async def cmd_breakdown(message: Message, user_id: UUID) -> None:
    async with SessionLocal() as db:
        countries = await analytics_service.get_owner_by_country(db, user_id)
        devices = await analytics_service.get_owner_by_device(db, user_id)
        browsers = await analytics_service.get_owner_by_browser(db, user_id)
        referrers = await analytics_service.get_owner_by_referrer(db, user_id)

    await message.answer(format_breakdown(countries, devices, browsers, referrers))


@router.message(F.text)
@authorized_handler
async def cmd_unknown(message: Message, user_id: UUID) -> None:
    await message.answer(format_unknown_command())


async def send_daily_report(bot: Bot) -> None:
    async with SessionLocal() as db:
        users = await user_repo.list_telegram_linked(db)

        for user in users:
            try:
                count = await analytics_service.get_owner_clicks_today(db, user.id)
                top_links = await analytics_service.get_owner_top_links_today(db, user.id)
                await bot.send_message(
                    user.telegram_chat_id, format_period("Daily Report", count, top_links)
                )
            except Exception:
                logger.exception("Failed to send daily report for user_id=%s", user.id)


async def send_weekly_report(bot: Bot) -> None:
    async with SessionLocal() as db:
        users = await user_repo.list_telegram_linked(db)

        for user in users:
            try:
                count = await analytics_service.get_owner_clicks_this_week(db, user.id)
                top_links = await analytics_service.get_owner_top_links_this_week(db, user.id)
                await bot.send_message(
                    user.telegram_chat_id, format_period("Weekly Report", count, top_links)
                )
            except Exception:
                logger.exception("Failed to send weekly report for user_id=%s", user.id)


async def main() -> None:
    if settings.TELEGRAM_BOT_TOKEN is None:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_report, CronTrigger(hour=9, minute=0), args=[bot])
    scheduler.add_job(
        send_weekly_report, CronTrigger(day_of_week="mon", hour=9, minute=0), args=[bot]
    )
    scheduler.start()

    logger.info("Telegram bot starting polling")
    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Telegram bot crashed")


if __name__ == "__main__":
    asyncio.run(main())

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_telegram_chat_id(db: AsyncSession, telegram_chat_id: int) -> User | None:
    result = await db.execute(
        select(User).where(User.telegram_chat_id == telegram_chat_id)
    )
    return result.scalar_one_or_none()


async def list_telegram_linked(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).where(User.telegram_chat_id.is_not(None)))
    return list(result.scalars().all())


async def set_telegram_chat_id(db: AsyncSession, user_id: UUID, telegram_chat_id: int) -> None:
    await db.execute(
        update(User).where(User.id == user_id).values(telegram_chat_id=telegram_chat_id)
    )


async def create(db: AsyncSession, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)

    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    return user


async def delete(db: AsyncSession, email: str) -> None:
    user = await get_by_email(db, email)

    if user is not None:
        await db.delete(user)
        await db.flush()

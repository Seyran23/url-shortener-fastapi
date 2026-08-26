from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


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

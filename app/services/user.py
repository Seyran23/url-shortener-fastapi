from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.user import UserCreate


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

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await user_repo.get_by_email(db, email)

    if user is None:
        raise InvalidCredentialsError()

    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()

    return user


async def delete_user(db: AsyncSession, email: str) -> None:
    user = await user_repo.get_by_email(db, email)

    if user is None:
        raise UserNotFoundError()

    await db.delete(user)
    await db.commit()


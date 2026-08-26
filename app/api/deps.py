from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import LOGIN_PATH
from app.core.exceptions import InvalidCredentialsError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories import user as user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=LOGIN_PATH, auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if token is None:
        raise InvalidCredentialsError()

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise InvalidCredentialsError()

    email = payload.get("sub")

    if not isinstance(email, str):
        raise InvalidCredentialsError()

    user = await user_repo.get_by_email(db, email)

    if user is None:
        raise InvalidCredentialsError()

    return user

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AUTH_PREFIX
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import RegisterResponse, UserCreate, UserResponse
from app.services.user import authenticate_user, register_user

router = APIRouter(prefix=AUTH_PREFIX, tags=["auth"])


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, user_in)

    access_token = create_access_token({"sub": user.email})

    user_response = UserResponse.model_validate(user)

    return RegisterResponse(user=user_response, token=Token(access_token=access_token))


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token({"sub": user.email})
    return Token(access_token=access_token)

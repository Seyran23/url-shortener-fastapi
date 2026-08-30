from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.core.constants import USERS_PREFIX
from app.models.user import User
from app.schemas.user import TelegramLinkCodeResponse, UserResponse
from app.services import user as user_service

router = APIRouter(prefix=USERS_PREFIX, tags=["users"])


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/telegram-link-code",
    response_model=TelegramLinkCodeResponse,
    status_code=status.HTTP_200_OK,
)
async def create_telegram_link_code(current_user: User = Depends(get_current_user)):
    code, expires_in_seconds = await user_service.generate_telegram_link_code(current_user.id)
    return TelegramLinkCodeResponse(code=code, expires_in_seconds=expires_in_seconds)

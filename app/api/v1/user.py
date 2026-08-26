from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.core.constants import USERS_PREFIX
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix=USERS_PREFIX, tags=["users"])


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

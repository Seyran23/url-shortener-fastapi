from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.link import router as link_router
from app.api.v1.user import router as user_router
from app.core.constants import API_V1_PREFIX

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(link_router)
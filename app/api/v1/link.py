from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.constants import LINKS_PREFIX
from app.core.rate_limit import rate_limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.links import LinkCreate, LinkResponse, LinkUpdate
from app.services import link as link_service

router = APIRouter(prefix=LINKS_PREFIX, tags=["links"])


@router.post(
    path="",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limiter(max_requests=20, window_seconds=60))],
)
async def create_link(
    link_data: LinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await link_service.create(db, current_user.id, link_data)


@router.get(path="", response_model=list[LinkResponse], status_code=status.HTTP_200_OK)
async def get_owned_links(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await link_service.list_for_owner(db, current_user.id, skip, limit)


@router.get(
    path="/{link_id}", response_model=LinkResponse, status_code=status.HTTP_200_OK
)
async def get_owned(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await link_service.get_owned(db, link_id, current_user.id)


@router.patch(
    path="/{link_id}", response_model=LinkResponse, status_code=status.HTTP_200_OK
)
async def update_link(
    link_id: UUID,
    link_update: LinkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await link_service.get_owned(db, link_id, current_user.id)
    fields = link_update.model_dump(exclude_unset=True)
    return await link_service.update_link(db, link, **fields)


@router.post("/{link_id}/activate", response_model=LinkResponse)
async def activate_link(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await link_service.get_owned(db, link_id, current_user.id)
    return await link_service.activate_link(db, link)


@router.post("/{link_id}/deactivate", response_model=LinkResponse)
async def deactivate_link(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await link_service.get_owned(db, link_id, current_user.id)
    return await link_service.deactivate_link(db, link)


@router.delete(path="/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await link_service.get_owned(db, link_id, current_user.id)
    await link_service.delete(db, link)

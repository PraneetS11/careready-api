from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.db.session import get_session
from app.models.users import User
from app.schemas.sites import SiteCreate, SiteRead, SiteUpdate
from app.services.sites import SiteService

router = APIRouter(dependencies=[Depends(RoleChecker(["coordinator", "admin"]))])
site_service = SiteService()
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[SiteRead])
async def get_all_sites(session: Session, active: bool | None = None):
    return await site_service.get_all_sites(session, active)


@router.get("/{site_id}", response_model=SiteRead)
async def get_site(site_id: UUID, session: Session):
    site = await site_service.get_site(site_id, session)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SiteRead,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def create_site(
    site_data_input: SiteCreate, session: Session, user: User = Depends(get_current_user)
):
    return await site_service.create_site(site_data_input, session, creator=user)


@router.patch("/{site_id}", response_model=SiteRead, dependencies=[Depends(RoleChecker(["admin"]))])
async def update_site(site_id: UUID, site_update_data: SiteUpdate, session: Session):
    site = await site_service.update_site(site_id, site_update_data, session)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def delete_site(site_id: UUID, session: Session):
    site = await site_service.delete_site(site_id, session)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

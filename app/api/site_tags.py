from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker
from app.db.session import get_session
from app.schemas.site_tags import SiteTagCreate, SiteTagRead
from app.services.site_tags import SiteTagService

router = APIRouter(dependencies=[Depends(RoleChecker(["coordinator", "admin"]))])
service = SiteTagService()


@router.post(
    "/tags",
    response_model=SiteTagRead,
    status_code=201,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def create_tag(data: SiteTagCreate, session: AsyncSession = Depends(get_session)):
    return await service.create_tag(data, session)


@router.get("/sites/{site_id}/tags", response_model=list[SiteTagRead])
async def list_tags(site_id: UUID, session: AsyncSession = Depends(get_session)):
    return await service.list_tags(site_id, session)


@router.post(
    "/sites/{site_id}/tags/{tag_id}",
    response_model=SiteTagRead,
    dependencies=[Depends(RoleChecker(["admin"]))],
)
async def attach_tag(site_id: UUID, tag_id: UUID, session: AsyncSession = Depends(get_session)):
    return await service.attach_tag(site_id, tag_id, session)

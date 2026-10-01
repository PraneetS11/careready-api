from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.db.session import get_session
from app.models.users import User
from app.schemas.site_notes import SiteNoteCreate, SiteNoteRead
from app.services.site_notes import SiteNoteService

router = APIRouter(dependencies=[Depends(RoleChecker(["coordinator", "admin"]))])
service = SiteNoteService()


@router.get("/sites/{site_id}/notes", response_model=list[SiteNoteRead])
async def list_notes(site_id: UUID, session: AsyncSession = Depends(get_session)):
    return await service.list_notes(site_id, session)


@router.post("/sites/{site_id}/notes", response_model=SiteNoteRead, status_code=201)
async def create_note(
    site_id: UUID,
    data: SiteNoteCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await service.create_note(site_id, user.id, data, session)

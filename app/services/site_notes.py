from sqlmodel import select

from app.errors import SiteNotFound
from app.models import Site, SiteNote


class SiteNoteService:
    async def require_site(self, site_id, session):
        if await session.get(Site, site_id) is None:
            raise SiteNotFound()

    async def list_notes(self, site_id, session):
        await self.require_site(site_id, session)
        result = await session.execute(
            select(SiteNote)
            .where(SiteNote.site_id == site_id)
            .order_by(SiteNote.created_at, SiteNote.id)
        )
        return result.scalars().all()

    async def create_note(self, site_id, user_id, data, session):
        await self.require_site(site_id, session)
        note = SiteNote(**data.model_dump(), site_id=site_id, author_user_id=user_id)
        try:
            session.add(note)
            await session.commit()
            await session.refresh(note)
        except Exception:
            await session.rollback()
            raise
        return note

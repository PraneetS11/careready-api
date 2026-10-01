from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models import SiteTag, SiteTagLink
from app.services.site_notes import SiteNoteService


class SiteTagService:
    async def create_tag(self, data, session):
        tag = SiteTag(**data.model_dump())
        try:
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(409, "Tag name already exists") from None
        except Exception:
            await session.rollback()
            raise
        return tag

    async def list_tags(self, site_id, session):
        await SiteNoteService().require_site(site_id, session)
        result = await session.execute(
            select(SiteTag)
            .join(SiteTagLink)
            .where(SiteTagLink.site_id == site_id)
            .order_by(SiteTag.name)
        )
        return result.scalars().all()

    async def attach_tag(self, site_id, tag_id, session):
        await SiteNoteService().require_site(site_id, session)
        tag = await session.get(SiteTag, tag_id)
        if tag is None:
            raise HTTPException(404, "Tag not found")
        try:
            await session.execute(
                insert(SiteTagLink).values(site_id=site_id, tag_id=tag_id).on_conflict_do_nothing()
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        return tag

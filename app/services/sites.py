from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.errors import SiteNotFound
from app.models.sites import Site
from app.schemas.sites import SiteCreate, SiteUpdate


class SiteService:
    async def get_all_sites(self, session: AsyncSession, active: bool | None = None):
        statement = select(Site).order_by(Site.id)
        if active is not None:
            statement = statement.where(Site.active == active)
        result = await session.execute(statement)
        return result.scalars().all()

    async def get_site(self, site_id: UUID, session: AsyncSession):
        result = await session.execute(select(Site).where(Site.id == site_id))
        site = result.scalars().first()
        if site is None:
            raise SiteNotFound()
        return site

    async def create_site(self, data: SiteCreate, session: AsyncSession, creator=None):
        site = Site(**data.model_dump(), created_by_user_id=creator.id if creator else None)
        site.creator = creator
        try:
            session.add(site)
            await session.commit()
            await session.refresh(site)
        except Exception:
            await session.rollback()
            raise
        return site

    async def update_site(self, site_id: UUID, data: SiteUpdate, session: AsyncSession):
        site = await self.get_site(site_id, session)
        try:
            site.active = data.active
            await session.commit()
            await session.refresh(site)
        except Exception:
            await session.rollback()
            raise
        return site

    async def delete_site(self, site_id: UUID, session: AsyncSession):
        site = await self.get_site(site_id, session)
        try:
            await session.delete(site)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        return site

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class SiteTagLink(SQLModel, table=True):
    site_id: UUID = Field(foreign_key="site.id", primary_key=True, ondelete="CASCADE")
    tag_id: UUID = Field(foreign_key="sitetag.id", primary_key=True, ondelete="CASCADE")


class SiteTag(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True)
    sites: list["Site"] = Relationship(
        back_populates="tags",
        link_model=SiteTagLink,
        sa_relationship_kwargs={"passive_deletes": True},
    )


if TYPE_CHECKING:
    from app.models.sites import Site

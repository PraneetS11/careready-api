from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.models.site_tags import SiteTagLink


class Site(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    city: str
    timezone: str
    active: bool = True

    created_by_user_id: UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    creator: "User" = Relationship(
        back_populates="sites", sa_relationship_kwargs={"lazy": "selectin"}
    )
    notes: list["SiteNote"] = Relationship(
        back_populates="site", sa_relationship_kwargs={"passive_deletes": "all"}
    )
    tags: list["SiteTag"] = Relationship(
        back_populates="sites",
        link_model=SiteTagLink,
        sa_relationship_kwargs={"passive_deletes": True},
    )


if TYPE_CHECKING:
    from app.models.site_notes import SiteNote
    from app.models.site_tags import SiteTag
    from app.models.users import User

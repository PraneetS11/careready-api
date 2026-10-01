from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel


class SiteNote(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    site_id: UUID = Field(foreign_key="site.id", ondelete="CASCADE")
    author_user_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    text: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    site: "Site" = Relationship(back_populates="notes")
    author: "User" = Relationship(back_populates="notes")


if TYPE_CHECKING:
    from app.models.sites import Site
    from app.models.users import User

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True)
    role: str = Field(
        default="coordinator",
        sa_column=Column(String, nullable=False, server_default="coordinator"),
    )
    is_active: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, server_default="true")
    )

    password_hash: str
    is_verified: bool = False
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    )

    sites: list["Site"] = Relationship(
        back_populates="creator", sa_relationship_kwargs={"passive_deletes": "all"}
    )
    notes: list["SiteNote"] = Relationship(
        back_populates="author", sa_relationship_kwargs={"passive_deletes": "all"}
    )


if TYPE_CHECKING:
    from app.models.site_notes import SiteNote
    from app.models.sites import Site

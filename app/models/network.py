"""Care network records; agency ownership is explicit on every operational record."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel


class Agency(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="user.id", unique=True)
    name: str
    city: str


class CareProfile(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    name: str
    agency_id: UUID | None = Field(default=None, foreign_key="agency.id", index=True)
    experience: int = 0
    gender: str = "undisclosed"
    services: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    languages: list[str] = Field(
        default_factory=lambda: ["English"], sa_column=Column(JSON, nullable=False)
    )
    approved: bool = False


class CareVisit(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    series_id: UUID = Field(default_factory=uuid4, index=True)
    agency_id: UUID = Field(foreign_key="agency.id", index=True)
    requester_id: UUID = Field(foreign_key="user.id", index=True)
    provider_id: UUID | None = Field(default=None, foreign_key="user.id", index=True)
    service: str
    recipient: str
    address: str
    city: str
    timezone: str
    latitude: float
    longitude: float
    starts_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    duration_minutes: int
    min_experience: int = 0
    gender_preference: str = "any"
    preferred_language: str = "any"
    communication: str = "standard"
    smoke_free: bool = True
    pets_present: bool = False
    status: str = "requested"
    notes: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class CareDevice(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agency_id: UUID = Field(foreign_key="agency.id", index=True)
    name: str
    asset_code: str
    status: str = "available"


class CareEvent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    visit_id: UUID = Field(foreign_key="carevisit.id", index=True)
    actor_id: UUID = Field(foreign_key="user.id")
    action: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

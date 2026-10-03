from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.users import UserCreate

SERVICES = {
    "companionship": "Companionship",
    "personal_care": "Personal support",
    "nursing": "Nursing visit",
    "respite": "Respite care",
}
# Public map positions are city centroids, never recipient coordinates.
CITIES = {
    "Toronto": (43.6532, -79.3832, "America/Toronto"),
    "Vancouver": (49.2827, -123.1207, "America/Vancouver"),
    "Montreal": (45.5019, -73.5674, "America/Toronto"),
    "London": (51.5074, -0.1278, "Europe/London"),
    "New York": (40.7128, -74.006, "America/New_York"),
    "Sydney": (-33.8688, 151.2093, "Australia/Sydney"),
}


class Register(UserCreate):
    role: Literal["requester", "provider", "agency"]
    name: str = Field(min_length=2, max_length=100, pattern=r"^[^\x00]*$")
    agency_name: str = Field(default="", max_length=100)
    city: str = "Toronto"
    agency_id: UUID | None = None
    experience: int = Field(default=0, ge=0, le=3)
    gender: Literal["woman", "man", "nonbinary", "undisclosed"] = "undisclosed"
    services: list[Literal["companionship", "personal_care", "nursing", "respite"]] = Field(
        default_factory=list, max_length=4
    )

    languages: list[
        Literal[
            "English",
            "French",
            "Spanish",
            "Mandarin",
            "Cantonese",
            "Hindi",
            "Punjabi",
            "Arabic",
            "Portuguese",
            "Other",
        ]
    ] = Field(default_factory=lambda: ["English"], min_length=1, max_length=10)

    @model_validator(mode="after")
    def validate_role(self):
        if self.city not in CITIES:
            raise ValueError("Select a supported city")
        if self.role == "agency" and len(self.agency_name.strip()) < 2:
            raise ValueError("Agency name is required")
        if self.role == "provider" and (not self.agency_id or not self.services):
            raise ValueError("Providers need an agency and at least one service")
        return self


class VisitCreate(BaseModel):
    agency_id: UUID
    service: Literal["companionship", "personal_care", "nursing", "respite"]
    recipient: str = Field(min_length=2, max_length=100, pattern=r"^[^\x00]*$")
    address: str = Field(min_length=5, max_length=250, pattern=r"^[^\x00]*$")
    city: str
    starts_at: datetime
    duration_minutes: int = Field(default=60, ge=30, le=240, multiple_of=30)
    min_experience: int = Field(default=0, ge=0, le=3)
    gender_preference: Literal["any", "woman", "man", "nonbinary"] = "any"
    preferred_language: Literal[
        "any",
        "English",
        "French",
        "Spanish",
        "Mandarin",
        "Cantonese",
        "Hindi",
        "Punjabi",
        "Arabic",
        "Portuguese",
        "Other",
    ] = "any"
    communication: Literal["standard", "slow_clear", "written"] = "standard"
    smoke_free: bool = True
    pets_present: bool = False
    occurrences: int = Field(default=1, ge=1, le=12)
    notes: str = Field(default="", max_length=1500, pattern=r"^[^\x00]*$")
    consent_confirmed: Literal[True]

    @model_validator(mode="after")
    def valid_time(self):
        if self.city not in CITIES:
            raise ValueError("Select a supported city")
        if self.starts_at.tzinfo is None or self.starts_at <= datetime.now(timezone.utc):
            raise ValueError("Choose a future time with a timezone")
        if self.starts_at > datetime.now(timezone.utc) + timedelta(days=365):
            raise ValueError("Visits must start within the next year")
        return self


class DeviceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, pattern=r"^[^\x00]*$")
    asset_code: str = Field(min_length=2, max_length=40, pattern=r"^[^\x00]*$")
    status: Literal["available", "in_use", "maintenance"] = "available"


class DeviceState(BaseModel):
    status: Literal["available", "in_use", "maintenance"]


class Approval(BaseModel):
    approved: bool


class Transition(BaseModel):
    action: Literal["publish", "cancel", "start", "complete"]

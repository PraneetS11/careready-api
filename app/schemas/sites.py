from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SiteCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Cedar Care Hamilton",
                    "city": "Hamilton",
                    "timezone": "America/Toronto",
                    "active": True,
                }
            ]
        }
    )
    name: str = Field(pattern=r"^[^\x00]*$")
    city: str = Field(pattern=r"^[^\x00]*$")
    timezone: str = Field(pattern=r"^[^\x00]*$")
    active: bool = True


class CreatorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str


class SiteRead(SiteCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_user_id: UUID | None = None
    creator: CreatorRead | None = None


class SiteUpdate(BaseModel):
    active: bool

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SiteCreate(BaseModel):
    name: str
    city: str
    timezone: str
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

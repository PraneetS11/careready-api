from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SiteCreate(BaseModel):
    name: str
    city: str
    timezone: str
    active: bool = True


class SiteRead(SiteCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class SiteUpdate(BaseModel):
    active: bool

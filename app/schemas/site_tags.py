from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SiteTagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80, pattern=r".*\S.*")


class SiteTagRead(SiteTagCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID

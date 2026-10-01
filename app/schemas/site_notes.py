from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SiteNoteCreate(BaseModel):
    text: str = Field(min_length=1, max_length=4000, pattern=r".*\S.*")


class SiteNoteRead(SiteNoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    site_id: UUID
    author_user_id: UUID
    created_at: datetime

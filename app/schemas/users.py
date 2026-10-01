from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    """Public account fields; stored password hashes never belong in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    is_verified: bool
    created_at: datetime

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from app.core.security import normalize_email


class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=6, max_length=1024)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_input(cls, value):
        return normalize_email(value) if isinstance(value, str) else value


class UserRead(BaseModel):
    """Public account fields; stored password hashes never belong in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: str = "coordinator"
    is_active: bool = True
    is_verified: bool
    created_at: datetime


class UserLogin(UserCreate):
    """Same normalized email/password input as signup, without public account fields."""


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

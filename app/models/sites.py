from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Site(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    city: str
    timezone: str
    active: bool = True

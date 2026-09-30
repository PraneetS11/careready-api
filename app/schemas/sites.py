from pydantic import BaseModel


class SiteCreate(BaseModel):
    name: str
    city: str
    timezone: str
    active: bool = True


class SiteUpdate(BaseModel):
    active: bool
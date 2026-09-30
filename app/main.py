from contextlib import asynccontextmanager
from typing import Optional

from fastapi.exceptions import HTTPException
from fastapi import FastAPI, Header, status
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.health import router
from app.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_async_engine(config.database_url, pool_pre_ping=True)
        cache = Redis.from_url(
            config.redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

        app.state.engine = engine
        app.state.sessions = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        app.state.redis = cache

        try:
            yield
        finally:
            await cache.aclose()
            await engine.dispose()

    app = FastAPI(
        title=config.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(router)

    return app


app = create_app()


@app.get("/")
async def read_root():
    return {"message": "CareReady API"}


@app.get("/practice/sites/{site_name}/welcome")
async def greet_site(site_name: str) -> dict:
    return {"message": f"Welcome to the {site_name} office!!"}


@app.get("/practice/site-preview")
async def preview_site(
    city: str = "Hamilton",
    active: bool = True,
) -> dict:
    return {
        "city": city,
        "active": active,
    }


class SiteCreateModel(BaseModel):
    name: str
    city: str
    timezone: str
    active: bool = True


@app.post("/create_site")
async def create_site_preview(site_data: SiteCreateModel) -> dict:
    return {
        "name": site_data.name,
        "city": site_data.city,
        "timezone": site_data.timezone,
        "active": site_data.active,
    }


@app.get("/practice/headers")
async def get_headers(
    accept: Optional[str] = Header(None),
    content_type: Optional[str] = Header(None),
    host: Optional[str] = Header(None),
) -> dict:
    return {
        "Accept": accept,
        "Content-Type": content_type,
        "Host": host,
    }


sites = [
    {
        "id": 1,
        "name": "McMaster",
        "city": "Hamilton",
        "timezone": "Eastern",
        "active": True,
    },
    {
        "id": 2,
        "name": "TMU",
        "city": "Toronto",
        "timezone": "Eastern",
        "active": False,
    },
]

next_id = 3


class Site(BaseModel):
    name: str
    city: str
    timezone: str
    active: bool


class SiteUpdateModel(BaseModel):
    active: bool


@app.get("/sites")
async def get_all_sites(
    active: bool | None = None,
) -> list[dict]:
    if active is None:
        return sites

    return [
        site
        for site in sites
        if site["active"] == active
    ]


@app.get("/sites/{site_id}")
async def get_site(site_id: int) -> dict:
    for site in sites:
        if site["id"] == site_id:
            return site

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Site not found",
    )


@app.post(
    "/sites",
    status_code=status.HTTP_201_CREATED,
)
async def create_site(site_data: Site) -> dict:
    global next_id

    new_site = site_data.model_dump()
    new_site["id"] = next_id

    next_id += 1

    sites.append(new_site)

    return new_site


@app.patch("/sites/{site_id}")
async def update_site(
    site_id: int,
    site_update_data: SiteUpdateModel,
) -> dict:
    for site in sites:
        if site["id"] == site_id:
            site["active"] = site_update_data.active
            return site

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Site not found",
    )


@app.delete(
    "/sites/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_site(site_id: int):
    for site in sites:
        if site["id"] == site_id:
            sites.remove(site)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Site not found",
    )
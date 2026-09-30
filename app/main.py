from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.health import router as health_router
from app.api.sites import router as sites_router
from app.core.config import Settings
from app.db.init_db import init_db


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_async_engine(
            config.database_url,
            pool_pre_ping=True,
        )

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
            if config.environment == "development":
                await init_db(engine)
            yield
        finally:
            await cache.aclose()
            await engine.dispose()

    app = FastAPI(
        title=config.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router)

    app.include_router(
        sites_router,
        prefix="/api/v1/sites",
        tags=["sites"],
    )

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
async def create_site_preview(
    site_data: SiteCreateModel,
) -> dict:
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

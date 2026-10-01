from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.auth import router as auth_router
from app.api.email_routes import router as email_router
from app.api.health import router as health_router
from app.api.site_notes import router as notes_router
from app.api.site_tags import router as tags_router
from app.api.sites import router as sites_router
from app.core.config import Settings
from app.errors import register_error_handlers
from app.middleware import register_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if config.environment != "test" and config.jwt_secret_key is None:
            raise ValueError("Configure JWT_SECRET_KEY in the environment before starting the API")
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
            yield
        finally:
            await cache.aclose()
            await engine.dispose()

    app = FastAPI(
        title=config.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    register_error_handlers(app)
    register_middleware(app, config)
    app.state.settings = config

    app.include_router(notes_router, prefix="/api/v1", tags=["site notes"])
    app.include_router(tags_router, prefix="/api/v1", tags=["site tags"])
    app.include_router(email_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

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

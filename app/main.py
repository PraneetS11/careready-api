from contextlib import asynccontextmanager

from fastapi import FastAPI
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
        version="0.2.0",
        description=(
            "A single-organization site operations API. Verified coordinators read sites "
            "and create notes; admins manage sites and tags. Bearer access tokens are "
            "required for business endpoints. Mail is queued to a local sandbox worker. "
            "Multi-tenancy and equipment-readiness workflows are planned."
        ),
        openapi_tags=[
            {"name": "auth", "description": "Signup, login, verification and password recovery."},
            {
                "name": "sites",
                "description": "Site CRUD: admins write; verified coordinators read.",
            },
            {"name": "site notes", "description": "Fictional operational notes scoped to a site."},
            {"name": "site tags", "description": "Shared categories attached to sites."},
            {"name": "health", "description": "Liveness and dependency readiness."},
        ],
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

    @app.get("/", tags=["health"])
    async def root():
        return {"message": config.app_name}

    return app


app = create_app()

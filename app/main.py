from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.health import router
from app.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_async_engine(config.database_url, pool_pre_ping=True)
        cache = Redis.from_url(config.redis_url, socket_connect_timeout=2, socket_timeout=2)
        app.state.engine = engine
        app.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
        app.state.redis = cache
        try:
            yield
        finally:
            await cache.aclose()
            await engine.dispose()

    app = FastAPI(title=config.app_name, version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
@app.get("/")
async def read_root():
    return {"message": "CareReady API"}
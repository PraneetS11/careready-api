from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel

from app.models.sites import Site  # noqa: F401 - register the table before create_all


async def init_db(engine: AsyncEngine) -> None:
    """Create missing local development tables; Alembic will replace this later."""
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

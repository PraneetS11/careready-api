"""Promote one existing fictional local account; run with python -m scripts.promote_admin EMAIL."""

import asyncio
import sys

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.models.users import User

engine = create_async_engine(Settings().database_url)


async def main(email):
    engine.echo = False
    try:
        async with engine.begin() as connection:
            ids = (
                (await connection.execute(select(User.id).where(User.email == email)))
                .scalars()
                .all()
            )
            if len(ids) != 1:
                raise ValueError("Expected exactly one existing account")
            await connection.execute(update(User).where(User.id == ids[0]).values(role="admin"))
        print("Selected local account promoted to admin")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))

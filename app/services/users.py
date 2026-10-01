from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

from app.core.security import hash_password, normalize_email
from app.models.users import User
from app.schemas.users import UserCreate


class DuplicateEmailError(Exception):
    """An account already uses this normalized email."""


class UserService:
    async def get_user_by_id(self, user_id: UUID, session: AsyncSession) -> User | None:
        return await session.get(User, user_id)

    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        result = await session.execute(select(User).where(User.email == normalize_email(email)))
        return result.scalars().first()

    async def create_user(self, data: UserCreate, session: AsyncSession) -> User:
        email = normalize_email(str(data.email))
        if await self.get_user_by_email(email, session) is not None:
            raise DuplicateEmailError
        password_hash = await run_in_threadpool(hash_password, data.password.get_secret_value())
        user = User(email=email, password_hash=password_hash)
        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        except IntegrityError:
            await session.rollback()
            # The unique constraint handles signups racing after the initial lookup.
            if await self.get_user_by_email(email, session) is not None:
                raise DuplicateEmailError from None
            raise
        except Exception:
            await session.rollback()
            raise
        return user

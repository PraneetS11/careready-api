from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_session
from app.db.token_store import token_in_blocklist
from app.models.users import User

bearer = HTTPBearer(auto_error=False)


def unauthorized():
    return HTTPException(
        401, "Invalid or missing credentials", headers={"WWW-Authenticate": "Bearer"}
    )


async def require_token(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
):
    data = (
        decode_token(credentials.credentials, request.app.state.settings) if credentials else None
    )
    if data is None:
        raise unauthorized()
    try:
        revoked = await token_in_blocklist(request.app.state.redis, data["jti"])
    except RedisError:
        raise HTTPException(503, "Authentication service unavailable") from None
    if revoked:
        raise unauthorized()
    return data


async def require_access_token(data: dict = Depends(require_token)):
    if data["token_type"] != "access":
        raise unauthorized()
    return data


async def require_refresh_token(data: dict = Depends(require_token)):
    if data["token_type"] != "refresh":
        raise unauthorized()
    return data


async def get_current_user(
    token: dict = Depends(require_access_token), session: AsyncSession = Depends(get_session)
) -> User:
    user = await session.get(User, UUID(token["sub"]))
    if user is None or not user.is_active:
        raise unauthorized()
    return user


class RoleChecker:
    def __init__(self, allowed_roles):
        self.allowed_roles = frozenset(allowed_roles)

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if not user.is_verified:
            raise HTTPException(403, "Verify your email before using this action")
        if user.role not in self.allowed_roles:
            raise HTTPException(403, "You are not allowed to perform this action")
        return user

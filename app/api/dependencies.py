from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError

from app.core.security import decode_token
from app.db.token_store import token_in_blocklist

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

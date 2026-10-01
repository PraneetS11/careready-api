from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import require_refresh_token, require_token, unauthorized
from app.core.security import create_token, verify_password
from app.db.session import get_session
from app.db.token_store import add_jti_to_blocklist
from app.schemas.users import AccessToken, TokenPair, UserCreate, UserLogin, UserRead
from app.services.users import DuplicateEmailError, UserService

router = APIRouter()
user_service = UserService()


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(data: UserCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await user_service.create_user(data, session)
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with email already exists",
        ) from None


@router.post("/login", response_model=TokenPair)
async def login(data: UserLogin, request: Request, session: AsyncSession = Depends(get_session)):
    user = await user_service.get_user_by_email(str(data.email), session)
    if user is None or not await run_in_threadpool(
        verify_password, data.password.get_secret_value(), user.password_hash
    ):
        raise HTTPException(
            401, "Invalid email or password", headers={"WWW-Authenticate": "Bearer"}
        )
    settings = request.app.state.settings
    return {
        "access_token": create_token(user.id, settings),
        "refresh_token": create_token(user.id, settings, "refresh"),
    }


@router.post("/refresh", response_model=AccessToken)
async def refresh(
    request: Request,
    token: dict = Depends(require_refresh_token),
    session: AsyncSession = Depends(get_session),
):
    user = await user_service.get_user_by_id(UUID(token["sub"]), session)
    if user is None:
        raise unauthorized()
    return {"access_token": create_token(user.id, request.app.state.settings)}


@router.post("/logout")
async def logout(request: Request, token: dict = Depends(require_token)):
    try:
        await add_jti_to_blocklist(request.app.state.redis, token["jti"], token["exp"])
    except RedisError:
        raise HTTPException(503, "Authentication service unavailable") from None
    return {"message": "Logged out successfully"}

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.users import UserCreate, UserRead
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

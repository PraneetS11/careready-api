import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, SecretStr, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.security import hash_password as generate_password_hash
from app.db.session import get_session
from app.email_tokens import create_email_token, read_email_token
from app.mail import send_mail
from app.models.users import User
from app.services.users import UserService

router = APIRouter()
service = UserService()


class EmailRequest(BaseModel):
    email: EmailStr


class ResetConfirm(BaseModel):
    password: SecretStr = Field(min_length=6, max_length=1024)
    password_confirm: SecretStr

    @model_validator(mode="after")
    def matching_passwords(self):
        if self.password.get_secret_value() != self.password_confirm.get_secret_value():
            raise ValueError("Passwords must match")
        pass
        return self


def settings_for(request):
    return request.app.state.settings


def secret_for(settings):
    return settings.jwt_secret_key


async def send_account_link(user, settings, purpose):
    token = create_email_token(secret_for(settings), user.id, purpose)
    action = "verify" if purpose == "verify" else "password-reset-confirm"
    link = settings.public_base_url.rstrip("/") + "/api/v1/auth/" + action + "/" + token
    await send_mail(
        settings,
        user.email,
        "Verify your account" if purpose == "verify" else "Reset your password",
        "Use this expiring link: " + link,
    )


@router.get("/verify/{token}")
async def verify(token: str, request: Request, session: AsyncSession = Depends(get_session)):
    settings = settings_for(request)
    uid = read_email_token(secret_for(settings), token, "verify", settings.mail_link_seconds)
    user = await session.get(User, uid)
    if user is None or not user.is_active:
        raise HTTPException(400, "Invalid or expired email link")
    if user.is_verified:
        return {"message": "Account already verified"}
    user.is_verified = True
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return {"message": "Account verified"}


@router.post("/verification-request")
async def verification_request(
    data: EmailRequest, request: Request, session: AsyncSession = Depends(get_session)
):
    user = await service.get_user_by_email(str(data.email), session)
    if user is not None and user.is_active and not user.is_verified:
        try:
            await send_account_link(user, settings_for(request), "verify")
        except HTTPException:
            logging.getLogger("account_mail").error("Sandbox account email delivery failed")
    return {"message": "If eligible, check the sandbox for verification instructions"}


@router.post("/password-reset-request")
async def reset_request(
    data: EmailRequest, request: Request, session: AsyncSession = Depends(get_session)
):
    user = await service.get_user_by_email(str(data.email), session)
    if user is not None and user.is_active:
        try:
            await send_account_link(user, settings_for(request), "reset")
        except HTTPException:
            logging.getLogger("account_mail").error("Sandbox account email delivery failed")
    return {"message": "If eligible, check the sandbox for reset instructions"}


@router.post("/password-reset-confirm/{token}")
async def reset_confirm(
    token: str, data: ResetConfirm, request: Request, session: AsyncSession = Depends(get_session)
):
    settings = settings_for(request)
    uid = read_email_token(secret_for(settings), token, "reset", settings.mail_link_seconds)
    user = await session.get(User, uid)
    if user is None or not user.is_active:
        raise HTTPException(400, "Invalid or expired email link")
    user.password_hash = await run_in_threadpool(
        generate_password_hash, data.password.get_secret_value()
    )
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return {"message": "Password updated"}

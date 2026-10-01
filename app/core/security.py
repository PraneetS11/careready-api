from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

password_hasher = PasswordHash.recommended()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


# JWTs are signed, not encrypted: payloads contain identifiers, never passwords.


def create_token(subject: UUID, settings: Settings, token_type: str = "access") -> str:
    if token_type not in {"access", "refresh"}:
        raise ValueError("Unknown token type")
    if settings.jwt_secret_key is None:
        raise ValueError("JWT_SECRET_KEY must be configured")
    lifetime = (
        timedelta(minutes=settings.access_token_minutes)
        if token_type == "access"
        else timedelta(days=settings.refresh_token_days)
    )
    return jwt.encode(
        {
            "sub": str(subject),
            "exp": datetime.now(timezone.utc) + lifetime,
            "jti": str(uuid4()),
            "token_type": token_type,
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, settings: Settings) -> dict | None:
    if settings.jwt_secret_key is None:
        return None
    try:
        data = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "jti", "token_type"]},
        )
        UUID(data["sub"])
        UUID(data["jti"])
        if type(data["exp"]) is not int or data["token_type"] not in {"access", "refresh"}:
            return None
        return data
    except (jwt.PyJWTError, ValueError, TypeError, AttributeError):
        return None

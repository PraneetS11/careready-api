from uuid import UUID

from fastapi import HTTPException
from itsdangerous import BadData, URLSafeTimedSerializer


def serializer(secret, purpose):
    if purpose not in {"verify", "reset"}:
        raise ValueError("Unsupported email token purpose")
    return URLSafeTimedSerializer(secret.get_secret_value(), salt="careready-email-" + purpose)


def create_email_token(secret, user_id, purpose):
    return serializer(secret, purpose).dumps({"user_id": str(user_id)})


def read_email_token(secret, token, purpose, max_age):
    try:
        data = serializer(secret, purpose).loads(token, max_age=max_age)
        return UUID(data["user_id"])
    except (BadData, ValueError, KeyError, TypeError):
        raise HTTPException(400, "Invalid or expired email link") from None

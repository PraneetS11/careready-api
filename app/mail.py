"""Local sandbox transport. This module never relays to an external SMTP host."""

from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType


async def send_mail(settings, recipient: str, subject: str, body: str):
    config = ConnectionConfig(
        MAIL_USERNAME="",
        MAIL_PASSWORD="",
        MAIL_FROM="noreply@example.com",
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=False,
    )
    try:
        await FastMail(config).send_message(
            MessageSchema(
                recipients=[recipient], subject=subject, body=body, subtype=MessageType.plain
            )
        )
    except Exception:
        raise HTTPException(503, "Sandbox mail delivery failed") from None

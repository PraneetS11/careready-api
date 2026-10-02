import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import HTTPException
from pydantic import SecretStr, ValidationError

from app.api.email_routes import ResetConfirm
from app.email_tokens import create_email_token, read_email_token
from app.mail import send_mail


class EmailTests(unittest.IsolatedAsyncioTestCase):
    def test_signed_tokens_expire_and_are_purpose_separated(self):
        secret = SecretStr("test-email-secret-at-least-32-characters")
        uid = uuid4()
        with patch("itsdangerous.timed.time.time", return_value=1000):
            token = create_email_token(secret, uid, "verify")
        with patch("itsdangerous.timed.time.time", return_value=1001):
            self.assertEqual(read_email_token(secret, token, "verify", 60), uid)
            for bad, purpose in [(token + "tamper", "verify"), (token, "reset")]:
                with self.assertRaises(HTTPException):
                    read_email_token(secret, bad, purpose, 60)
        with patch("itsdangerous.timed.time.time", return_value=1061):
            with self.assertRaises(HTTPException):
                read_email_token(secret, token, "verify", 60)

    def test_password_confirmation_must_match(self):
        with self.assertRaises(ValidationError):
            ResetConfirm(password="good-password", password_confirm="different")

    async def test_delivery_failure_is_not_success(self):
        with patch(
            "app.mail.FastMail.send_message",
            new_callable=AsyncMock,
            side_effect=RuntimeError("private smtp data"),
        ):
            with self.assertRaises(HTTPException) as error:
                await send_mail(
                    SimpleNamespace(mail_server="127.0.0.1", mail_port=1027),
                    "fictional@example.com",
                    "Welcome",
                    "Fictional test",
                )
        self.assertEqual(error.exception.status_code, 503)
        self.assertNotIn("private", error.exception.detail)

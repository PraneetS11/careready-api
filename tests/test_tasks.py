import unittest
from unittest.mock import AsyncMock, patch

from app.tasks import send_email


class TaskTests(unittest.TestCase):
    def test_task_events_redact_message_arguments(self):
        with patch("celery.app.task.Task.apply_async") as publish:
            send_email.delay("test@example.com", "Subject", "secret-body")
        self.assertEqual(publish.call_args.kwargs["argsrepr"], "<redacted mail payload>")
        self.assertEqual(publish.call_args.kwargs["kwargsrepr"], "<redacted>")
        self.assertEqual(
            publish.call_args.kwargs["args"], ("test@example.com", "Subject", "secret-body")
        )

    def test_worker_confirms_only_successful_delivery(self):
        with patch("app.tasks.send_mail", new_callable=AsyncMock) as mail:
            result = send_email.run("test@example.com", "Subject", "Fictional")
        self.assertEqual(result, {"delivered_to_sandbox": True})
        mail.assert_awaited_once()

import asyncio

from celery import Celery, Task
from fastapi import HTTPException

from app.core.config import Settings
from app.mail import send_mail

settings = Settings()


class PrivateMailTask(Task):
    def apply_async(self, args=None, kwargs=None, **options):
        options.update(argsrepr="<redacted mail payload>", kwargsrepr="<redacted>")
        return super().apply_async(args=args, kwargs=kwargs, **options)


celery_app = Celery(
    "careready", broker=settings.celery_broker_url, backend=settings.celery_result_backend
)
celery_app.conf.update(
    task_default_queue="careready-mail",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    broker_connection_timeout=3,
    task_publish_retry=False,
)


@celery_app.task(base=PrivateMailTask, name="careready.send_email")
def send_email(recipient, subject, body):
    try:
        asyncio.run(send_mail(settings, recipient, subject, body))
    except HTTPException:
        raise RuntimeError("Sandbox mail delivery failed") from None
    return {"delivered_to_sandbox": True}

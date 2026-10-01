"""Local learning experiment; production auth routes use Celery instead."""

import asyncio

from fastapi import BackgroundTasks, FastAPI

from app.core.config import Settings
from app.mail import send_mail

settings = Settings()
app = FastAPI()


async def delayed_welcome():
    await asyncio.sleep(2)
    await send_mail(
        settings,
        "background-demo@example.com",
        "Background experiment",
        "Fictional in-process mail",
    )


@app.post("/demo", status_code=202)
async def demo(tasks: BackgroundTasks):
    tasks.add_task(delayed_welcome)
    return {"message": "Scheduled in this process; delivery is not yet confirmed"}

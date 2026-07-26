import asyncio
import uuid

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.tasks.celery_app import celery_app
from app.use_cases.run_pipeline import run_pipeline


@celery_app.task(name="run_video_pipeline", bind=True, max_retries=0)
def run_video_pipeline_task(self, job_id: str) -> None:
    async def _run():
        async with SessionLocal() as db:
            await run_pipeline(db, uuid.UUID(job_id))

    asyncio.run(_run())

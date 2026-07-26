import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.schemas.common import VideoJobCreate, VideoJobOut
from app.infrastructure.db.models import JobStatus, Script, VideoJob
from app.infrastructure.db.session import get_db
from app.infrastructure.tasks.pipeline_tasks import run_video_pipeline_task

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=VideoJobOut, status_code=201)
async def create_job(payload: VideoJobCreate, db: AsyncSession = Depends(get_db)):
    script = await db.get(Script, payload.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    job = VideoJob(script_id=payload.script_id, target_aspect_ratio=payload.target_aspect_ratio)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    run_video_pipeline_task.delay(str(job.id))
    return job


@router.get("", response_model=list[VideoJobOut])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VideoJob).order_by(VideoJob.created_at.desc()))
    return result.scalars().all()


@router.get("/{job_id}", response_model=VideoJobOut)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(VideoJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/cancel", response_model=VideoJobOut)
async def cancel_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(VideoJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in status {job.status}")
    job.status = JobStatus.cancelled
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/{job_id}/events")
async def job_events(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    async def event_stream():
        while True:
            job = await db.get(VideoJob, job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'job not found'})}\n\n"
                return
            payload = {
                "status": job.status.value,
                "current_stage": job.current_stage,
                "progress_percent": job.progress_percent,
                "output_video_url": job.output_video_url,
                "error_message": job.error_message,
            }
            yield f"data: {json.dumps(payload)}\n\n"
            if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
                return
            await asyncio.sleep(2)
            db.expire_all()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

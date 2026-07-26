import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.schemas.common import (
    ParsedLineOut,
    ParsedSceneOut,
    ScriptCreate,
    ScriptOut,
    ScriptParsePreview,
)
from app.infrastructure.db.models import Character, Script
from app.infrastructure.db.session import get_db
from app.use_cases.persist_parsed_script import parse_and_link_script
from app.use_cases.script_parser import parse_script

router = APIRouter(prefix="/api/scripts", tags=["scripts"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ScriptOut, status_code=201)
async def create_script(payload: ScriptCreate, db: AsyncSession = Depends(get_db)):
    script = Script(**payload.model_dump())
    db.add(script)
    await db.commit()
    await db.refresh(script)
    await parse_and_link_script(db, script)
    return script


@router.get("", response_model=list[ScriptOut])
async def list_scripts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Script))
    return result.scalars().all()


@router.get("/{script_id}", response_model=ScriptOut)
async def get_script(script_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.put("/{script_id}", response_model=ScriptOut)
async def update_script(script_id: uuid.UUID, payload: ScriptCreate, db: AsyncSession = Depends(get_db)):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    for field, value in payload.model_dump().items():
        setattr(script, field, value)
    await db.commit()
    await db.refresh(script)
    await parse_and_link_script(db, script)
    return script


@router.delete("/{script_id}", status_code=204)
async def delete_script(script_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    await db.delete(script)
    await db.commit()


@router.post("/parse-preview", response_model=ScriptParsePreview)
async def parse_preview(payload: ScriptCreate, db: AsyncSession = Depends(get_db)):
    """Non-persisting preview so the script editor can show speaker/language
    detection before the user saves or generates a video."""
    result = await db.execute(select(Character))
    known_names = {c.name for c in result.scalars().all()}
    parsed = parse_script(payload.raw_text, known_names)
    return ScriptParsePreview(
        scenes=[
            ParsedSceneOut(
                order=s.order,
                description=s.description,
                background_prompt=s.background_prompt,
                camera_notes=s.camera_notes,
            )
            for s in parsed.scenes
        ],
        lines=[
            ParsedLineOut(
                order=l.order,
                scene_order=l.scene_order,
                speaker_name=l.speaker_name,
                text=l.text,
                detected_language=l.detected_language,
                expression_tag=l.expression_tag,
            )
            for l in parsed.lines
        ],
        unmatched_speakers=sorted(parsed.unmatched_speakers),
    )

import base64
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.schemas.character import (
    CharacterCreate,
    CharacterOut,
    CharacterUpdate,
    VoiceProfileCreate,
    VoiceProfileOut,
)
from app.infrastructure.db.models import Character, ScriptLine, VoiceProfile
from app.infrastructure.db.session import get_db
from app.infrastructure.providers.storage.factory import get_storage_provider
from app.infrastructure.providers.storage.paths import new_tmp_path

router = APIRouter(
    prefix="/api/characters", tags=["characters"], dependencies=[Depends(get_current_user)]
)


@router.post("", response_model=CharacterOut, status_code=201)
async def create_character(payload: CharacterCreate, db: AsyncSession = Depends(get_db)):
    character = Character(**payload.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character, attribute_names=["voices"])
    return character


@router.get("", response_model=list[CharacterOut])
async def list_characters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).options(selectinload(Character.voices)))
    return result.scalars().all()


@router.get("/{character_id}", response_model=CharacterOut)
async def get_character(character_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    character = await db.get(Character, character_id, options=[selectinload(Character.voices)])
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.patch("/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: uuid.UUID, payload: CharacterUpdate, db: AsyncSession = Depends(get_db)
):
    character = await db.get(Character, character_id, options=[selectinload(Character.voices)])
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(character, field, value)
    await db.commit()
    await db.refresh(character, attribute_names=["voices"])
    return character


@router.delete("/{character_id}", status_code=204)
async def delete_character(character_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    voice_result = await db.execute(select(VoiceProfile).where(VoiceProfile.character_id == character_id))
    for voice in voice_result.scalars().all():
        await db.delete(voice)

    line_result = await db.execute(
        select(ScriptLine).where(ScriptLine.speaker_character_id == character_id)
    )
    for line in line_result.scalars().all():
        line.speaker_character_id = None

    await db.flush()
    await db.delete(character)
    await db.commit()


class AppearanceImageUpload(BaseModel):
    image_base64: str
    content_type: str = "image/png"


@router.post("/{character_id}/appearance-image", response_model=CharacterOut)
async def upload_appearance_image(
    character_id: uuid.UUID, payload: AppearanceImageUpload, db: AsyncSession = Depends(get_db)
):
    character = await db.get(Character, character_id, options=[selectinload(Character.voices)])
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    extension = ".png" if "png" in payload.content_type else ".jpg"
    tmp_path = new_tmp_path(extension)
    with open(tmp_path, "wb") as f:
        f.write(base64.b64decode(payload.image_base64))

    storage = get_storage_provider()
    url = await storage.save(tmp_path, f"characters/{character_id}{extension}")
    character.appearance_ref_image_url = url
    await db.commit()
    await db.refresh(character, attribute_names=["voices"])
    return character


@router.post("/{character_id}/voices", response_model=VoiceProfileOut, status_code=201)
async def add_voice(
    character_id: uuid.UUID, payload: VoiceProfileCreate, db: AsyncSession = Depends(get_db)
):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    voice = VoiceProfile(character_id=character_id, **payload.model_dump())
    db.add(voice)
    await db.commit()
    await db.refresh(voice)
    return voice

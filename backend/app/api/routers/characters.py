import uuid

from fastapi import APIRouter, Depends, HTTPException
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
from app.infrastructure.db.models import Character, VoiceProfile
from app.infrastructure.db.session import get_db

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
    await db.delete(character)
    await db.commit()


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

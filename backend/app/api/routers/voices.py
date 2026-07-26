import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.schemas.character import VoiceProfileOut
from app.infrastructure.db.models import Capability, VoiceProfile
from app.infrastructure.db.session import get_db
from app.infrastructure.providers.factory import ProviderFactory

router = APIRouter(prefix="/api/voices", tags=["voices"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[VoiceProfileOut])
async def list_voices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VoiceProfile))
    return result.scalars().all()


@router.delete("/{voice_id}", status_code=204)
async def delete_voice(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    voice = await db.get(VoiceProfile, voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    await db.delete(voice)
    await db.commit()


@router.post("/{voice_id}/preview")
async def preview_voice(
    voice_id: uuid.UUID, text: str = "Hello, this is a voice preview.", db: AsyncSession = Depends(get_db)
):
    voice = await db.get(VoiceProfile, voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    factory = ProviderFactory(db)
    provider = await factory.get(Capability.tts)
    result = await provider.synthesize(text, voice.provider_voice_id, voice.language)
    return {"audio_url": result.audio_url, "duration_seconds": result.duration_seconds}

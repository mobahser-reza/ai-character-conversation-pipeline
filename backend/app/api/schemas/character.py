import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VoiceProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    character_id: uuid.UUID
    provider: str
    provider_voice_id: str
    language: str
    sample_url: str | None
    created_at: datetime


class VoiceProfileCreate(BaseModel):
    provider: str
    provider_voice_id: str
    language: str
    sample_url: str | None = None


class CharacterCreate(BaseModel):
    name: str
    description: str = ""
    appearance_ref_image_url: str | None = None
    appearance_ref_video_url: str | None = None
    personality_profile: dict = {}


class CharacterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    appearance_ref_image_url: str | None = None
    appearance_ref_video_url: str | None = None
    personality_profile: dict | None = None
    default_voice_id: uuid.UUID | None = None


class CharacterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    appearance_ref_image_url: str | None
    appearance_ref_video_url: str | None
    personality_profile: dict
    default_voice_id: uuid.UUID | None
    created_at: datetime
    voices: list[VoiceProfileOut] = []

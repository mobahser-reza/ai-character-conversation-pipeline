import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.infrastructure.db.models import Capability, JobStatus, LanguageMode


class ApiKeyCreate(BaseModel):
    provider_name: str
    api_key: str


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_name: str
    is_active: bool
    created_at: datetime
    masked_key: str = "••••••••"


class ProviderConfigCreate(BaseModel):
    capability: Capability
    provider_name: str
    is_default: bool = True
    config: dict = {}


class ProviderConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    capability: Capability
    provider_name: str
    is_default: bool
    config: dict


class ScriptCreate(BaseModel):
    title: str
    raw_text: str
    language_mode: LanguageMode = LanguageMode.mixed


class ScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    raw_text: str
    language_mode: LanguageMode
    created_at: datetime
    updated_at: datetime


class ParsedLineOut(BaseModel):
    order: int
    scene_order: int
    speaker_name: str | None
    text: str
    detected_language: str
    expression_tag: str | None


class ParsedSceneOut(BaseModel):
    order: int
    description: str
    background_prompt: str
    camera_notes: str


class ScriptParsePreview(BaseModel):
    scenes: list[ParsedSceneOut]
    lines: list[ParsedLineOut]
    unmatched_speakers: list[str]


class VideoJobCreate(BaseModel):
    script_id: uuid.UUID
    target_aspect_ratio: str = "9:16"


class VideoJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    script_id: uuid.UUID
    status: JobStatus
    current_stage: str | None
    progress_percent: float
    target_aspect_ratio: str
    output_video_url: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

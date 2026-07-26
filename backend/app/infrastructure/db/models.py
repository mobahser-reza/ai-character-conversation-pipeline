import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_col():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class LanguageMode(str, enum.Enum):
    en = "en"
    hi = "hi"
    hinglish = "hinglish"
    mixed = "mixed"


class Capability(str, enum.Enum):
    tts = "tts"
    avatar = "avatar"
    video_gen = "video_gen"
    subtitles = "subtitles"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StageStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class AssetType(str, enum.Enum):
    audio = "audio"
    avatar_clip = "avatar_clip"
    background_clip = "background_clip"
    subtitle_file = "subtitle_file"
    final_video = "final_video"


class Character(Base):
    __tablename__ = "character"

    id: Mapped[uuid.UUID] = _uuid_col()
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    appearance_ref_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    appearance_ref_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    personality_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    default_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("voice_profile.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    voices: Mapped[list["VoiceProfile"]] = relationship(
        back_populates="character", foreign_keys="VoiceProfile.character_id"
    )


class VoiceProfile(Base):
    __tablename__ = "voice_profile"

    id: Mapped[uuid.UUID] = _uuid_col()
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("character.id"))
    provider: Mapped[str] = mapped_column(String(60))
    provider_voice_id: Mapped[str] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(20))
    sample_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    character: Mapped["Character"] = relationship(
        back_populates="voices", foreign_keys=[character_id]
    )


class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[uuid.UUID] = _uuid_col()
    provider_name: Mapped[str] = mapped_column(String(60), unique=True)
    key_encrypted: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ProviderConfig(Base):
    __tablename__ = "provider_config"

    id: Mapped[uuid.UUID] = _uuid_col()
    capability: Mapped[Capability] = mapped_column(Enum(Capability))
    provider_name: Mapped[str] = mapped_column(String(60))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)


class Script(Base):
    __tablename__ = "script"

    id: Mapped[uuid.UUID] = _uuid_col()
    title: Mapped[str] = mapped_column(String(200))
    raw_text: Mapped[str] = mapped_column(Text)
    language_mode: Mapped[LanguageMode] = mapped_column(Enum(LanguageMode), default=LanguageMode.mixed)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    scenes: Mapped[list["Scene"]] = relationship(back_populates="script", cascade="all, delete-orphan")
    lines: Mapped[list["ScriptLine"]] = relationship(back_populates="script", cascade="all, delete-orphan")


class Scene(Base):
    __tablename__ = "scene"

    id: Mapped[uuid.UUID] = _uuid_col()
    script_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("script.id"))
    order: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, default="")
    background_prompt: Mapped[str] = mapped_column(Text, default="")
    camera_notes: Mapped[str] = mapped_column(Text, default="")

    script: Mapped["Script"] = relationship(back_populates="scenes")
    lines: Mapped[list["ScriptLine"]] = relationship(back_populates="scene")


class ScriptLine(Base):
    __tablename__ = "script_line"

    id: Mapped[uuid.UUID] = _uuid_col()
    script_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("script.id"))
    scene_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scene.id"), nullable=True)
    order: Mapped[int] = mapped_column(Integer)
    speaker_character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("character.id"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text)
    detected_language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expression_tag: Mapped[str | None] = mapped_column(String(300), nullable=True)

    script: Mapped["Script"] = relationship(back_populates="lines")
    scene: Mapped["Scene"] = relationship(back_populates="lines")


class VideoJob(Base):
    __tablename__ = "video_job"

    id: Mapped[uuid.UUID] = _uuid_col()
    script_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("script.id"))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending)
    current_stage: Mapped[str | None] = mapped_column(String(60), nullable=True)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    target_aspect_ratio: Mapped[str] = mapped_column(String(10), default="9:16")
    output_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    stage_logs: Mapped[list["VideoJobStageLog"]] = relationship(
        back_populates="video_job", cascade="all, delete-orphan"
    )
    media_assets: Mapped[list["MediaAsset"]] = relationship(
        back_populates="video_job", cascade="all, delete-orphan"
    )


class VideoJobStageLog(Base):
    __tablename__ = "video_job_stage_log"

    id: Mapped[uuid.UUID] = _uuid_col()
    video_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_job.id"))
    stage_name: Mapped[str] = mapped_column(String(60))
    status: Mapped[StageStatus] = mapped_column(Enum(StageStatus), default=StageStatus.pending)
    provider_used: Mapped[str | None] = mapped_column(String(60), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    video_job: Mapped["VideoJob"] = relationship(back_populates="stage_logs")


class MediaAsset(Base):
    __tablename__ = "media_asset"

    id: Mapped[uuid.UUID] = _uuid_col()
    video_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_job.id"))
    type: Mapped[AssetType] = mapped_column(Enum(AssetType))
    url: Mapped[str] = mapped_column(String(500))
    stage_ref: Mapped[str | None] = mapped_column(String(60), nullable=True)

    video_job: Mapped["VideoJob"] = relationship(back_populates="media_assets")

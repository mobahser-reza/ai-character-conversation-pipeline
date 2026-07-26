"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voice_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(60), nullable=False),
        sa.Column("provider_voice_id", sa.String(200), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("sample_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "character",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("appearance_ref_image_url", sa.String(500), nullable=True),
        sa.Column("appearance_ref_video_url", sa.String(500), nullable=True),
        sa.Column("personality_profile", sa.JSON, nullable=False, server_default="{}"),
        sa.Column(
            "default_voice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("voice_profile.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_foreign_key(
        "fk_voice_profile_character", "voice_profile", "character", ["character_id"], ["id"]
    )

    op.create_table(
        "api_key",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_name", sa.String(60), nullable=False, unique=True),
        sa.Column("key_encrypted", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    capability_enum = postgresql.ENUM(
        "tts", "avatar", "video_gen", "subtitles", name="capability"
    )
    capability_enum.create(op.get_bind(), checkfirst=True)
    capability_enum.create_type = False
    op.create_table(
        "provider_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("capability", capability_enum, nullable=False),
        sa.Column("provider_name", sa.String(60), nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("config", sa.JSON, nullable=False, server_default="{}"),
    )

    language_mode_enum = postgresql.ENUM(
        "en", "hi", "hinglish", "mixed", name="languagemode"
    )
    language_mode_enum.create(op.get_bind(), checkfirst=True)
    language_mode_enum.create_type = False
    op.create_table(
        "script",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("language_mode", language_mode_enum, nullable=False, server_default="mixed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "scene",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("script_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("script.id"), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("background_prompt", sa.Text, nullable=False, server_default=""),
        sa.Column("camera_notes", sa.Text, nullable=False, server_default=""),
    )

    op.create_table(
        "script_line",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("script_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("script.id"), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scene.id"), nullable=True),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column(
            "speaker_character_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("character.id"),
            nullable=True,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("detected_language", sa.String(20), nullable=True),
        sa.Column("expression_tag", sa.String(300), nullable=True),
    )

    job_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed", "cancelled", name="jobstatus"
    )
    job_status_enum.create(op.get_bind(), checkfirst=True)
    job_status_enum.create_type = False
    op.create_table(
        "video_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("script_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("script.id"), nullable=False),
        sa.Column("status", job_status_enum, nullable=False, server_default="pending"),
        sa.Column("current_stage", sa.String(60), nullable=True),
        sa.Column("progress_percent", sa.Float, nullable=False, server_default="0"),
        sa.Column("target_aspect_ratio", sa.String(10), nullable=False, server_default="9:16"),
        sa.Column("output_video_url", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    stage_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed", "skipped", name="stagestatus"
    )
    stage_status_enum.create(op.get_bind(), checkfirst=True)
    stage_status_enum.create_type = False
    op.create_table(
        "video_job_stage_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "video_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("video_job.id"), nullable=False
        ),
        sa.Column("stage_name", sa.String(60), nullable=False),
        sa.Column("status", stage_status_enum, nullable=False, server_default="pending"),
        sa.Column("provider_used", sa.String(60), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
    )

    asset_type_enum = postgresql.ENUM(
        "audio", "avatar_clip", "background_clip", "subtitle_file", "final_video", name="assettype"
    )
    asset_type_enum.create(op.get_bind(), checkfirst=True)
    asset_type_enum.create_type = False
    op.create_table(
        "media_asset",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "video_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("video_job.id"), nullable=False
        ),
        sa.Column("type", asset_type_enum, nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("stage_ref", sa.String(60), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("media_asset")
    op.drop_table("video_job_stage_log")
    op.drop_table("video_job")
    op.drop_table("script_line")
    op.drop_table("scene")
    op.drop_table("script")
    op.drop_table("provider_config")
    op.drop_table("api_key")
    op.drop_constraint("fk_voice_profile_character", "voice_profile", type_="foreignkey")
    op.drop_table("character")
    op.drop_table("voice_profile")
    sa.Enum(name="assettype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="stagestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="languagemode").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="capability").drop(op.get_bind(), checkfirst=True)

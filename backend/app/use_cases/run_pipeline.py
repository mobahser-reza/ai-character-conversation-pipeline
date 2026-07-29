import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    AssetType,
    Capability,
    Character,
    JobStatus,
    MediaAsset,
    Scene,
    Script,
    ScriptLine,
    StageStatus,
    VideoJob,
    VideoJobStageLog,
    VoiceProfile,
)
from app.infrastructure.providers.factory import ProviderFactory
from app.infrastructure.providers.storage.factory import get_storage_provider
from app.infrastructure.providers.storage.paths import media_url_to_local_path, new_tmp_path
from app.use_cases import compositor

STAGES = ["tts", "avatar", "background", "composite", "subtitles", "export"]


async def _start_stage(db: AsyncSession, job: VideoJob, stage_name: str) -> VideoJobStageLog:
    job.current_stage = stage_name
    job.progress_percent = STAGES.index(stage_name) / len(STAGES) * 100
    log = VideoJobStageLog(
        video_job_id=job.id,
        stage_name=stage_name,
        status=StageStatus.running,
        started_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    return log


async def _finish_stage(db: AsyncSession, log: VideoJobStageLog, provider_name: str) -> None:
    log.status = StageStatus.completed
    log.provider_used = provider_name
    log.finished_at = datetime.now(timezone.utc)
    await db.commit()


async def _fail_stage(db: AsyncSession, job: VideoJob, log: VideoJobStageLog, error: str) -> None:
    log.status = StageStatus.failed
    log.error = error
    log.finished_at = datetime.now(timezone.utc)
    job.status = JobStatus.failed
    job.error_message = error
    await db.commit()


async def run_pipeline(db: AsyncSession, job_id: uuid.UUID) -> None:
    job = await db.get(VideoJob, job_id)
    if job is None:
        raise ValueError(f"VideoJob {job_id} not found")

    script = await db.get(
        Script,
        job.script_id,
        options=[selectinload(Script.scenes), selectinload(Script.lines)],
    )
    characters_by_id = {
        c.id: c for c in (await db.execute(select(Character))).scalars().all()
    }
    voices_by_character: dict[uuid.UUID, list[VoiceProfile]] = {}
    for voice in (await db.execute(select(VoiceProfile))).scalars().all():
        voices_by_character.setdefault(voice.character_id, []).append(voice)

    def resolve_voice_id(character: Character | None, language: str) -> str:
        if character is None:
            return "default"
        candidates = voices_by_character.get(character.id, [])
        if not candidates:
            return "default"
        for voice in candidates:
            if voice.language == language:
                return voice.provider_voice_id
        return candidates[0].provider_voice_id

    job.status = JobStatus.running
    await db.commit()

    factory = ProviderFactory(db)
    storage = get_storage_provider()

    try:
        lines = sorted(script.lines, key=lambda l: l.order)
        scenes = {s.id: s for s in script.scenes}

        # Stage 1: TTS per line
        log = await _start_stage(db, job, "tts")
        tts_provider = await factory.get(Capability.tts)
        line_audio: dict[uuid.UUID, dict] = {}
        for line in lines:
            character = characters_by_id.get(line.speaker_character_id) if line.speaker_character_id else None
            language = line.detected_language or "en"
            voice_id = resolve_voice_id(character, language)
            result = await tts_provider.synthesize(line.text, voice_id, language)
            db.add(MediaAsset(video_job_id=job.id, type=AssetType.audio, url=result.audio_url, stage_ref="tts"))
            line_audio[line.id] = {"url": result.audio_url, "duration": result.duration_seconds}
        await db.commit()
        await _finish_stage(db, log, tts_provider.name)

        # Stage 2: Avatar clip per line
        log = await _start_stage(db, job, "avatar")
        avatar_provider = await factory.get(Capability.avatar)
        line_avatar: dict[uuid.UUID, str] = {}
        for line in lines:
            character = characters_by_id.get(line.speaker_character_id) if line.speaker_character_id else None
            ref_image = character.appearance_ref_image_url if character else ""
            audio = line_audio[line.id]
            result = await avatar_provider.generate_clip(
                ref_image or "", audio["url"], line.expression_tag, job.target_aspect_ratio
            )
            db.add(MediaAsset(video_job_id=job.id, type=AssetType.avatar_clip, url=result.video_url, stage_ref="avatar"))
            line_avatar[line.id] = result.video_url
        await db.commit()
        await _finish_stage(db, log, avatar_provider.name)

        # Stage 3: Background clip per scene
        log = await _start_stage(db, job, "background")
        video_gen_provider = await factory.get(Capability.video_gen)
        scene_background: dict[uuid.UUID, str] = {}
        for scene in scenes.values():
            scene_lines = [l for l in lines if l.scene_id == scene.id]
            duration = sum(line_audio[l.id]["duration"] for l in scene_lines) or 3.0
            result = await video_gen_provider.generate_background(
                scene.background_prompt or scene.description, scene.camera_notes, duration, job.target_aspect_ratio
            )
            db.add(MediaAsset(video_job_id=job.id, type=AssetType.background_clip, url=result.video_url, stage_ref="background"))
            scene_background[scene.id] = result.video_url
        await db.commit()
        await _finish_stage(db, log, video_gen_provider.name)

        # Stage 4: Composite - both characters share the same frame per scene (left/right),
        # whoever's speaking is lip-synced, the other shown as a still, concat in script order
        log = await _start_stage(db, job, "composite")
        canvas_width, canvas_height = compositor.canvas_size(job.target_aspect_ratio)

        scene_character_side: dict[uuid.UUID, dict[uuid.UUID, str]] = {}
        for scene in scenes.values():
            scene_lines = [l for l in lines if l.scene_id == scene.id]
            ordered_characters: list[uuid.UUID] = []
            for l in scene_lines:
                if l.speaker_character_id and l.speaker_character_id not in ordered_characters:
                    ordered_characters.append(l.speaker_character_id)
            scene_character_side[scene.id] = {
                cid: ("left" if i == 0 else "right") for i, cid in enumerate(ordered_characters[:2])
            }

        other_character_image_paths: dict[uuid.UUID, str] = {}

        async def local_image_path(character: Character) -> str:
            if character.id in other_character_image_paths:
                return other_character_image_paths[character.id]
            tmp_path = new_tmp_path(".jpg")
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(character.appearance_ref_image_url)
                response.raise_for_status()
            with open(tmp_path, "wb") as f:
                f.write(response.content)
            other_character_image_paths[character.id] = tmp_path
            return tmp_path

        composited_clips = []
        for line in lines:
            background_url = scene_background[line.scene_id]
            background_path = media_url_to_local_path(background_url)
            avatar_path = media_url_to_local_path(line_avatar[line.id])
            out_path = new_tmp_path(".mp4")

            sides = scene_character_side[line.scene_id]
            speaker_side = sides.get(line.speaker_character_id) if line.speaker_character_id else None
            other_cid = next((cid for cid in sides if cid != line.speaker_character_id), None)
            other_character = characters_by_id.get(other_cid) if other_cid else None

            if speaker_side and other_character and other_character.appearance_ref_image_url:
                other_image_path = await local_image_path(other_character)
                compositor.overlay_two_avatars_on_background(
                    background_path, canvas_width, canvas_height,
                    avatar_path, other_image_path, speaker_side, out_path,
                )
            else:
                compositor.overlay_avatar_on_background(background_path, avatar_path, out_path)
            composited_clips.append(out_path)

        concat_path = new_tmp_path(".mp4")
        compositor.concat_clips(composited_clips, concat_path)
        await _finish_stage(db, log, "ffmpeg")

        # Stage 5: Subtitles
        log = await _start_stage(db, job, "subtitles")
        subtitle_provider = await factory.get(Capability.subtitles)
        cursor = 0.0
        srt_lines = []
        for line in lines:
            duration = line_audio[line.id]["duration"]
            srt_lines.append({"start": cursor, "end": cursor + duration, "text": line.text})
            cursor += duration
        subtitle_result = await subtitle_provider.generate(srt_lines, script.language_mode.value)
        db.add(MediaAsset(video_job_id=job.id, type=AssetType.subtitle_file, url=subtitle_result.srt_url, stage_ref="subtitles"))
        await db.commit()

        srt_path = media_url_to_local_path(subtitle_result.srt_url)
        subtitled_path = new_tmp_path(".mp4")
        compositor.burn_subtitles(concat_path, srt_path, subtitled_path)
        await _finish_stage(db, log, subtitle_provider.name)

        # Stage 6: Final export
        log = await _start_stage(db, job, "export")
        final_path = new_tmp_path(".mp4")
        compositor.export_final(subtitled_path, final_path, job.target_aspect_ratio)
        final_url = await storage.save(final_path, f"final/{job.id}.mp4")
        db.add(MediaAsset(video_job_id=job.id, type=AssetType.final_video, url=final_url, stage_ref="export"))
        job.output_video_url = final_url
        job.status = JobStatus.completed
        job.progress_percent = 100.0
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await _finish_stage(db, log, "ffmpeg")

    except Exception as exc:  # noqa: BLE001 - pipeline stage failures must be persisted, not raised bare
        current_log_result = await db.execute(
            select(VideoJobStageLog)
            .where(VideoJobStageLog.video_job_id == job.id, VideoJobStageLog.status == StageStatus.running)
            .order_by(VideoJobStageLog.started_at.desc())
        )
        current_log = current_log_result.scalars().first()
        if current_log:
            await _fail_stage(db, job, current_log, str(exc))
        else:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            await db.commit()
        raise

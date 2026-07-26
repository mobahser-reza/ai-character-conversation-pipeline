# Architecture

## Goal

Script in, social-media-ready video out. Two permanent AI characters with consistent
appearance, voice, and personality. Every pipeline stage (voice, lip-sync, expression,
camera, background, subtitles, export) is behind a swappable provider interface so new
vendors (HeyGen, Kling, Veo, Hedra, Runway, ElevenLabs, ...) drop in without touching
orchestration code.

## Layers (Clean Architecture)

```
domain/            Entities and interfaces (ports). No framework code, no I/O.
  interfaces/providers.py   TTSProvider, AvatarProvider, VideoGenProvider,
                             SubtitleProvider, StorageProvider (all ABCs)

use_cases/         Orchestration logic. Depends only on domain interfaces.
  script_parser.py          Speaker/scene/camera/expression/language extraction
  persist_parsed_script.py  Re-parses a Script row into Scene/ScriptLine rows
  run_pipeline.py           The 6-stage video generation pipeline (see below)
  compositor.py             ffmpeg overlay/concat/subtitle-burn/export helpers

infrastructure/     Concrete adapters implementing the domain interfaces.
  providers/{tts,avatar,video_gen,subtitles}/local_stub.py   Zero-cost dev/dry-run
  providers/tts/elevenlabs.py, providers/avatar/heygen.py,
  providers/video_gen/runway.py                               Real vendor adapters
  providers/storage/{local_disk,s3}.py                        Storage backends
  providers/factory.py       ProviderFactory — resolves capability -> active adapter
  db/models.py                SQLAlchemy models (see schema below)
  tasks/                      Celery app + the pipeline task

api/                FastAPI routers + Pydantic schemas. Thin — calls use_cases only.
core/                Config (pydantic-settings), JWT auth, Fernet key encryption.
```

## Provider swap mechanism

Every pipeline stage maps to a `Capability` enum (`tts`, `avatar`, `video_gen`,
`subtitles`). The `provider_config` table stores which concrete provider is the
`is_default` one for each capability. `ProviderFactory.get(capability)` reads that
row and instantiates the matching class from an in-memory registry
(`app/infrastructure/providers/factory.py`).

**To add a new provider**: write one adapter file implementing the relevant ABC from
`domain/interfaces/providers.py`, add one line to `_load_registries()` in
`factory.py`, and select it in the dashboard's API Keys & Providers page. Nothing
else changes — this is the Open/Closed principle in practice.

Every provider capability defaults to `local_stub`, which renders placeholder
media (silent WAV, solid-color MP4 with a text overlay, valid SRT) using only
`ffmpeg` — no external key, no cost. This lets the full pipeline run end-to-end
before any real vendor key is configured.

## Database schema

| Table | Purpose |
|---|---|
| `character` | Name, description, appearance reference (image/video), personality profile (JSON), default voice |
| `voice_profile` | One or more TTS voices per character, per provider, per language |
| `api_key` | Fernet-encrypted vendor API keys |
| `provider_config` | Active provider per capability (the swap mechanism) |
| `script` | Raw script text + language mode |
| `scene` | Parsed `SCENE:`/`CAMERA:` blocks: description, background prompt, camera notes |
| `script_line` | One dialogue line: speaker, text, detected language, expression tag |
| `video_job` | One generation run: status, current stage, progress %, output URL |
| `video_job_stage_log` | Per-stage audit trail: provider used, timing, errors |
| `media_asset` | Every intermediate/final file produced (audio, avatar clip, background clip, subtitles, final video) |

## Script format

```
SCENE: A cozy modern living room, warm lighting, medium shot
[Aryan] (smiling, leaning forward): Hey, kaise ho aap?
[Meera] (curious, arms crossed): I'm good yaar, just thinking about our next trip.
CAMERA: slow zoom in
```

- `[Name]` — speaker, matched against `character.name` (case-sensitive exact match)
- `(...)` — optional expression/body-language tag, passed to the avatar provider
- `SCENE:` — starts a new scene; its text becomes the background-generation prompt
- `CAMERA:` — camera movement note for the current scene, appended to the background prompt
- Any other line — treated as scene description/narration

Language per line is auto-detected (`use_cases/script_parser.py::detect_language`):
Devanagari script → `hi`; Latin-script text with romanized Hindi words mixed with
English → `hinglish`; otherwise falls back to `langdetect`.

## Pipeline stages (Celery task, one per `VideoJob`)

1. **tts** — synthesize audio per script line (character's assigned voice + detected language)
2. **avatar** — lip-synced avatar clip per line (character's reference image + that line's audio + expression tag)
3. **background** — one generated background clip per scene (prompt + camera notes + total scene duration + aspect ratio)
4. **composite** — ffmpeg overlays each avatar clip onto its scene's background, concatenates in script order
5. **subtitles** — burns SRT (soft file also kept as a `media_asset`) generated from cumulative line durations
6. **export** — final encode to the target aspect ratio (9:16 / 1:1 / 16:9), H.264 + faststart

Each stage writes a `video_job_stage_log` row and updates `video_job.progress_percent`;
the dashboard polls `GET /api/jobs/{id}` every 2s to show live progress.

## Known limitation (local storage + ffmpeg compositing)

The compositor (`use_cases/compositor.py`) shells out to `ffmpeg` on files resolved
from `/media/<key>` back to local disk paths (`storage/paths.py`). This works
out of the box with the default `local` storage backend. If you switch
`STORAGE_BACKEND=s3`, the compositor stage needs to download intermediate clips
locally first — that download step isn't wired yet (flagged as a follow-up, not
needed for local Docker Compose deployment).

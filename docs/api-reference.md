# API Reference

Base URL: `http://localhost:8000` (direct) or via the frontend's rewrite proxy at
`http://localhost:3000/api/...`. Interactive OpenAPI docs: `http://localhost:8000/docs`.

All endpoints except `/api/auth/login` and `/api/health` require
`Authorization: Bearer <token>`.

## Auth

`POST /api/auth/login` — form-encoded `username`, `password` (from `ADMIN_USERNAME`/
`ADMIN_PASSWORD` env vars). Returns `{ access_token, token_type }`.

## Characters

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/api/characters` | `CharacterCreate` | name, description, appearance_ref_image_url, personality_profile |
| GET | `/api/characters` | — | list all, with nested voices |
| GET | `/api/characters/{id}` | — | |
| PATCH | `/api/characters/{id}` | `CharacterUpdate` | partial update |
| DELETE | `/api/characters/{id}` | — | |
| POST | `/api/characters/{id}/voices` | `VoiceProfileCreate` | attach a voice (provider, provider_voice_id, language) |

## Voices

| Method | Path | Notes |
|---|---|---|
| GET | `/api/voices` | list all voice profiles |
| DELETE | `/api/voices/{id}` | |
| POST | `/api/voices/{id}/preview?text=...` | runs the active TTS provider, returns `{ audio_url, duration_seconds }` |

## API Keys & Providers

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/api/api-keys` | `{ provider_name, api_key }` | upserts, encrypts at rest (Fernet) |
| GET | `/api/api-keys` | — | masked list |
| DELETE | `/api/api-keys/{id}` | — | |
| POST | `/api/providers` | `{ capability, provider_name, is_default, config }` | sets the active adapter for a capability |
| GET | `/api/providers` | — | list all provider configs |

`capability` is one of `tts`, `avatar`, `video_gen`, `subtitles`.

## Scripts

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/api/scripts` | `ScriptCreate` | saves + immediately parses into scenes/lines |
| GET | `/api/scripts` | — | |
| GET | `/api/scripts/{id}` | — | |
| PUT | `/api/scripts/{id}` | `ScriptCreate` | replaces text, re-parses |
| DELETE | `/api/scripts/{id}` | — | |
| POST | `/api/scripts/parse-preview` | `{ title, raw_text }` | non-persisting: returns parsed scenes/lines/unmatched speakers, for the editor's live preview |

## Jobs

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/api/jobs` | `{ script_id, target_aspect_ratio }` | creates a `VideoJob`, enqueues the Celery pipeline task |
| GET | `/api/jobs` | — | history, newest first |
| GET | `/api/jobs/{id}` | — | status/progress/output_video_url |
| POST | `/api/jobs/{id}/cancel` | — | marks cancelled (does not kill an in-flight Celery task) |
| GET | `/api/jobs/{id}/events` | — | Server-Sent Events stream of the same status payload every 2s |

`target_aspect_ratio` is one of `9:16`, `1:1`, `16:9`.

## Health

`GET /api/health` — `{ "status": "ok" }`, no auth required. Used for container healthchecks.

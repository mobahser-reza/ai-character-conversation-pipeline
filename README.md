# AI Character Conversation Pipeline

Script-in, social-media-ready-video-out production framework. Two permanent AI
characters, consistent across every video. Swap AI vendors (HeyGen, Kling, Veo,
ElevenLabs, Hedra, Runway, ...) without touching orchestration code.

## Quick start

```bash
cp .env.example .env   # fill in JWT_SECRET_KEY, ENCRYPTION_MASTER_KEY, admin creds
docker compose up --build
```

Open `http://localhost:3000`, log in, and follow `docs/training-guide.md`.

Everything runs in zero-cost stub mode until you add real provider keys via the
dashboard's **API Keys** page — see `docs/training-guide.md` step 1.

## Docs

- `docs/architecture.md` — system design, DB schema, provider swap mechanism
- `docs/api-reference.md` — every endpoint
- `docs/training-guide.md` — step-by-step workflow to produce a video, start to finish
- `docs/video-production-log/` — write-up per produced sample video

## Stack

FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL + Celery + Redis (backend/worker),
Next.js 14 + Tailwind (frontend), Docker Compose for local deployment.

## Repo layout

```
backend/app/
  domain/           entities + provider interfaces (ports)
  use_cases/        script parser, pipeline orchestration, ffmpeg compositor
  infrastructure/   provider adapters, DB models/session, Celery
  api/              FastAPI routers + Pydantic schemas
  core/             config, JWT auth, Fernet key encryption
frontend/app/       Next.js dashboard (characters, voices, scripts, jobs, docs)
docs/               architecture, API reference, training guide, video logs
```

## Tests

```bash
docker compose run --rm backend pytest
```

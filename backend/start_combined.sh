#!/bin/sh
set -e

alembic upgrade head

celery -A app.infrastructure.tasks.celery_app.celery_app worker --loglevel=info --concurrency=1 --pool=solo &

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

#!/bin/sh
set -eu

cd /app

echo "Bootstrapping users table (required before Alembic 001)…"
python - <<'PY'
from app.core.database import Base, engine
from app.models.user import User

Base.metadata.create_all(bind=engine, tables=[User.__table__])
print("users table ready")
PY

echo "Running Alembic migrations…"
alembic upgrade head

PORT="${PORT:-8000}"
echo "Starting uvicorn on 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"

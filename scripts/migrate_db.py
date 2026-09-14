"""One-time migration helper for managed Postgres (Neon / Vercel Postgres / etc.).

Usage (from repo root, with DATABASE_URL set — never commit real secrets):

  cd backend
  python ../scripts/migrate_db.py

Or:

  cd backend
  alembic upgrade head

On Vercel, run migrations once after provisioning the database (CLI/local),
not on every serverless invocation.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from alembic import command
from alembic.config import Config

from app.core.database import Base, engine
from app.models.user import User


def main() -> None:
    print("Bootstrapping users table (required before Alembic 001)…")
    Base.metadata.create_all(bind=engine, tables=[User.__table__])

    cfg = Config(str(_BACKEND / "alembic.ini"))
    # env.py reads DATABASE_URL / settings; script location is relative to cwd.
    print("Running alembic upgrade head…")
    command.upgrade(cfg, "head")
    print("Migrations complete.")


if __name__ == "__main__":
    # Run with cwd=backend so alembic relative paths resolve.
    import os

    os.chdir(_BACKEND)
    main()

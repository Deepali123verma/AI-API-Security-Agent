"""Apply Alembic migrations to managed Postgres (Neon / Vercel Postgres / etc.).

Usage (from repo root, with DATABASE_URL set — never commit real secrets):

  cd backend
  python ../scripts/migrate_db.py

On Vercel this also runs during the project build so Production/Preview
DATABASE_URL (available on the build machine) receives the schema. Do not
rely on a local .env that points at localhost when intending to migrate Neon.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.core.config import settings
from app.core.database import engine

REQUIRED_TABLES = ("users", "scans", "endpoints", "findings")


def _safe_target(database_url: str) -> str:
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgres://", "postgresql://"
    )
    parsed = urlparse(normalized)
    db_name = (parsed.path or "/").lstrip("/") or "(none)"
    host = parsed.hostname or "(none)"
    port = parsed.port or "(default)"
    return f"{host}:{port}/{db_name}"


def _verify_schema() -> None:
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = [name for name in REQUIRED_TABLES if name not in existing]
    if missing:
        raise RuntimeError(
            "Migration finished but required tables are missing: "
            + ", ".join(missing)
            + f". Existing tables: {sorted(existing) or '(none)'}"
        )

    # Confirm users is queryable (catches wrong search_path / empty schema issues).
    with engine.connect() as conn:
        conn.execute(text("SELECT 1 FROM users LIMIT 1"))


def main() -> None:
    target = _safe_target(settings.database_url)
    print(f"Migrating database target: {target}")

    if os.getenv("VERCEL") == "1" and target.startswith("localhost"):
        raise RuntimeError(
            "Refusing to migrate localhost while VERCEL=1. "
            "Set DATABASE_URL to your Neon connection string in the Vercel project."
        )

    cfg = Config(str(_BACKEND / "alembic.ini"))
    print("Running alembic upgrade head…")
    command.upgrade(cfg, "head")

    print("Verifying required tables…")
    _verify_schema()
    print("Migrations complete; schema verified.")


if __name__ == "__main__":
    os.chdir(_BACKEND)
    main()

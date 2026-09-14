from contextlib import asynccontextmanager
from pathlib import Path
import os

from dotenv import load_dotenv

# Load project-root `.env` before importing Settings-backed modules.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, health, scans
from app.core.config import get_cors_origins, get_static_dir
from app.core.database import Base, engine
from app.models import Endpoint, Finding, Scan, User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Vercel, schema is applied via scripts/migrate_db.py (one-time).
    # Avoid failing the whole serverless cold start on DDL/connect issues.
    if os.getenv("VERCEL") == "1":
        yield
        return

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI API Security Agent",
    description="Backend API for the AI API Security Agent project.",
    version="0.9.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(scans.router)

_static_dir = get_static_dir()
if _static_dir is not None:
    assets_dir = _static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """Serve the React SPA for non-API routes (single public URL deployments)."""
        if full_path:
            candidate = _static_dir / full_path
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(_static_dir / "index.html")

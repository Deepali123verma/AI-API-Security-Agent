from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load project-root `.env` before importing Settings-backed modules.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, scans
from app.core.config import get_cors_origins
from app.core.database import Base, engine
from app.models import Endpoint, Finding, Scan, User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
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

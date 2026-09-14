from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to the repo (not process CWD), so `uvicorn` from
# `backend/` still loads the project-root `.env` documented in the README.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(_PROJECT_ROOT / ".env"),
            str(_BACKEND_DIR / ".env"),
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    max_upload_size_bytes: int = 5 * 1024 * 1024
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.2
    gemini_max_bulk_findings: int = 10
    cors_origins: str = "http://localhost:5173"
    # Directory containing the Vite production build (index.html + assets).
    # Empty/unset disables SPA serving (API-only mode for local backend-only runs).
    static_dir: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        """Normalize managed-Postgres URLs for SQLAlchemy + psycopg.

        Also strips accidental wrapping/orphan quotes that break Neon query
        params (Vercel logs: invalid channel_binding value: \"require'\").
        """
        if not isinstance(value, str):
            return value

        url = value.strip()
        if len(url) >= 2 and url[0] == url[-1] and url[0] in {"'", '"'}:
            url = url[1:-1].strip()
        url = url.rstrip("'\"").strip()

        if url.startswith("postgres://"):
            url = "postgresql://" + url.removeprefix("postgres://")
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = "postgresql+psycopg://" + url.removeprefix("postgresql://")

        parsed = urlparse(url)
        if parsed.query:
            cleaned: list[tuple[str, str]] = []
            for key, raw_val in parse_qsl(parsed.query, keep_blank_values=True):
                val = raw_val.strip().strip("'\"")
                if key == "channel_binding" and val not in {"require", "prefer", "disable"}:
                    val = "prefer"
                cleaned.append((key, val))
            url = urlunparse(parsed._replace(query=urlencode(cleaned)))

        return url


settings = Settings()


def get_cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]


def get_static_dir() -> Path | None:
    if not settings.static_dir:
        return None
    path = Path(settings.static_dir)
    if path.is_dir() and (path / "index.html").is_file():
        return path
    return None

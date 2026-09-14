"""
Vercel FastAPI entrypoint.

Vercel looks for a FastAPI instance named `app` in supported files such as
`main.py` at the repository root. The real application lives under `backend/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.main import app  # noqa: E402

__all__ = ["app"]

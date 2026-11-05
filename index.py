"""Vercel entrypoint for the backend (see vercel.json and docs in README).

The FastAPI app lives in backend/app and imports itself as `app.*`, so backend/ goes on
sys.path. The project root is the repo root so that data/ is part of the deployment.
Locally and in Docker the app is started from backend/ as before (uvicorn app.main:app).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.main import app  # noqa: E402

__all__ = ["app"]

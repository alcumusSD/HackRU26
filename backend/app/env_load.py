"""Load backend/.env for local runs."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def load_app_env(*, override: bool = True) -> Path:
    """Load `backend/.env` if present. Override so model/key edits apply after restart."""
    env_path = _BACKEND_ROOT / ".env"
    load_dotenv(env_path, override=override)
    return env_path

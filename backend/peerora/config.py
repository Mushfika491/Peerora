"""Application settings, read from environment variables.

Real environment variables always win. For local development on your own
computer, backend/.env can supply values too (that file is ignored by Git).
In GitHub Codespaces, DATABASE_URL comes from a Codespaces secret.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv normally comes with fastapi[standard]
    load_dotenv = None

# The "backend" folder (the parent of the "peerora" package folder).
BACKEND_DIR = Path(__file__).resolve().parent.parent

if load_dotenv is not None:
    # override=False means values that already exist in the real environment
    # (for example Codespaces secrets) are never replaced by the .env file.
    load_dotenv(BACKEND_DIR / ".env", override=False)

DEFAULT_CORS_ORIGINS = ["http://localhost:5173"]


def get_database_url() -> str:
    """Return the SQLAlchemy database URL built from DATABASE_URL.

    Supabase provides a URL starting with "postgresql://". SQLAlchemy would
    then look for the older psycopg2 driver, so the prefix is changed to
    "postgresql+psycopg://", which selects Psycopg 3.
    """
    url = os.environ.get("DATABASE_URL", "").strip()

    if not url:
        # The message deliberately never includes the URL itself.
        raise RuntimeError(
            "DATABASE_URL is not set. Add it as a Codespaces secret, or put it "
            "in backend/.env for local development (see backend/.env.example)."
        )

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    return url


def get_cors_origins() -> list[str]:
    """Return the browser origins allowed to call this API.

    CORS_ORIGINS is a comma-separated list. Each origin is an address like
    https://example.com or http://localhost:5173, with no path and no trailing
    slash. If the variable is not set, only the local Vite server is allowed.
    """
    raw = os.environ.get("CORS_ORIGINS", "")
    origins = [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]

    if "*" in origins:
        raise ValueError(
            "CORS_ORIGINS must list real origins. A wildcard (*) is not allowed."
        )

    return origins if origins else list(DEFAULT_CORS_ORIGINS)
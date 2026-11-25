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

# ---- Authentication settings ----
# Secrets are read when needed (not at import time) so tests can provide them
# and so a missing value produces a clear error that never shows the value.

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "peerora"
MAX_ACCESS_TOKEN_MINUTES = 15  # the assessment allows at most 15 minutes
REFRESH_COOKIE_NAME = "peerora_refresh"
REFRESH_COOKIE_PATH = "/api/auth"
CSRF_HEADER_NAME = "X-Requested-With"
CSRF_HEADER_VALUE = "peerora"


def _required_secret(name: str, min_length: int) -> str:
    value = os.environ.get(name, "")
    if len(value) < min_length:
        raise RuntimeError(
            f"{name} is not set or is shorter than {min_length} characters. "
            "Set it as an environment variable (see backend/.env.example)."
        )
    return value


def get_jwt_secret() -> str:
    """Key that signs access tokens (HS256). At least 32 characters."""
    return _required_secret("JWT_SECRET_KEY", 32)


def get_password_pepper() -> str:
    """Server-side secret mixed into every password before hashing."""
    return _required_secret("PASSWORD_PEPPER", 16)


def validate_required_secrets() -> None:
    """Run at application startup, so a deployment with a missing or short
    secret fails immediately instead of at the first login. The error names
    the variable, never its value."""
    get_jwt_secret()
    get_password_pepper()


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def get_access_token_minutes() -> int:
    """Access-token lifetime, never longer than 15 minutes."""
    return max(1, min(_int_env("ACCESS_TOKEN_MINUTES", 15), MAX_ACCESS_TOKEN_MINUTES))


def get_refresh_token_days() -> int:
    return max(1, _int_env("REFRESH_TOKEN_DAYS", 7))


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def cookie_secure() -> bool:
    """Send the refresh cookie only over HTTPS. Set COOKIE_SECURE=false for
    local development over plain http://localhost."""
    return _bool_env("COOKIE_SECURE", True)


def trust_proxy_headers() -> bool:
    """Read the client IP from X-Forwarded-For only behind a trusted proxy.
    Vercel sets VERCEL=1 automatically and always overwrites that header."""
    return _bool_env("TRUST_PROXY_HEADERS", os.environ.get("VERCEL") == "1")


# ---- Email (password reset) ----
# EMAIL_BACKEND:
#   smtp   - send real email through an SMTP server (production)
#   outbox - write emails as files into EMAIL_OUTBOX_DIR (local development
#            only; refused on Vercel so reset links can never land on disk there,
#            and refused when DATABASE_URL is not SQLite, so a local backend
#            pointed at the real database cannot create real reset tokens by
#            accident. EMAIL_OUTBOX_ALLOW_REMOTE_DB=true allows it on purpose.)
#   unset  - email is not configured: password reset by email is reported as
#            unavailable instead of pretending an email was sent

EMAIL_BACKENDS = ("smtp", "outbox")


def get_email_backend() -> str | None:
    value = os.environ.get("EMAIL_BACKEND", "").strip().lower()
    return value if value in EMAIL_BACKENDS else None


def is_production_host() -> bool:
    return os.environ.get("VERCEL") == "1"


def get_email_outbox_dir() -> Path:
    return Path(os.environ.get("EMAIL_OUTBOX_DIR", str(BACKEND_DIR / "dev-outbox")))


def uses_local_database() -> bool:
    """True when DATABASE_URL is a local SQLite file (or in-memory database)."""
    return os.environ.get("DATABASE_URL", "").strip().startswith("sqlite")


def outbox_allowed_with_remote_database() -> bool:
    """Explicit opt-in for using the outbox against a non-SQLite database."""
    return _bool_env("EMAIL_OUTBOX_ALLOW_REMOTE_DB", False)


def get_smtp_settings() -> dict[str, object]:
    return {
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": _int_env("SMTP_PORT", 587),
        "username": os.environ.get("SMTP_USERNAME", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "sender": os.environ.get("EMAIL_FROM", "").strip(),
        "starttls": _bool_env("SMTP_STARTTLS", True),
        "ssl": _bool_env("SMTP_SSL", False),
    }


def get_public_app_url() -> str:
    """Base URL of the frontend, used to build links in emails (no trailing slash).
    Required in production; defaults to the Vite dev server locally."""
    value = os.environ.get("PUBLIC_APP_URL", "").strip().rstrip("/")
    if value:
        return value
    return "" if is_production_host() else "http://localhost:5173"

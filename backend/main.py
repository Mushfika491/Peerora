from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from peerora.config import CSRF_HEADER_NAME, get_cors_origins, validate_required_secrets
from peerora.core.dependencies import ERROR_CODE_HEADER
from peerora.core.request_info import CLIENT_BRAND_HEADER
from peerora.errors import unhandled_error_handler, validation_error_handler
from peerora.routers import (
    admin_audit,
    admin_content,
    admin_exports,
    admin_users,
    auth,
    dashboard,
    groups,
    records,
    tutors,
    users,
)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Refuse to start without JWT_SECRET_KEY and PASSWORD_PEPPER (values are never shown).
    validate_required_secrets()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Peerora API",
    description="REST API for Peerora - A University Peer Learning and Tutoring Platform",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)

# CORS: only the listed frontend origins. In production the frontend and the
# API share one origin (Vercel rewrites /api/*), so CORS is mainly for local
# development without the Vite proxy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,  # the refresh-token cookie
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization", CSRF_HEADER_NAME, CLIENT_BRAND_HEADER],
    expose_headers=["X-Total-Count", "Content-Disposition", ERROR_CODE_HEADER],
)


# API responses are data, never pages: nothing in them may load or run.
# (The interactive docs pages are excluded because they load Swagger UI/ReDoc
# from a CDN. The React app gets its own CSP at build time, see frontend/csp.ts.)
API_CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
DOCS_PATHS = ("/api/docs", "/api/redoc")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/") and not request.url.path.startswith(DOCS_PATHS):
        # API responses (often personal data) must not be cached by browsers or proxies.
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Content-Security-Policy", API_CONTENT_SECURITY_POLICY)
    return response


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Readable 422 messages, and a generic 500 that never exposes a stack trace.
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

for router_module in (auth, users, tutors, groups, records, dashboard,
                      admin_users, admin_content, admin_audit, admin_exports):
    app.include_router(router_module.router)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# Serve the frontend when the production build exists.
if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)

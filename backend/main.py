
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from peerora.config import get_cors_origins
from peerora.errors import validation_error_handler
from peerora.routers import tutors

app = FastAPI(
    title="Peerora API",
    description="REST API for Peerora - A University Peer Learning and Tutoring Platform",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello(name: str = "World") -> dict[str, str]:
    return {"message": f"Hello, {name}!"}


# Register validation error handler
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Register tutor profile CRUD routes
app.include_router(tutors.router)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# Serve the frontend when the production build exists.
if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)

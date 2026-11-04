from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from peerora.config import get_cors_origins
from peerora.errors import validation_error_handler
from peerora.routers import tutors

app = FastAPI(title="FastAPI + React")

# CORS: lets the browser accept responses from this API when the frontend runs
# on a different address (for example the Vite server on port 5173).
# The allowed addresses come from the CORS_ORIGINS environment variable.
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


# EXERCISE (part 1): uncomment to add POST /api/user, then test it at /docs.
# from pydantic import BaseModel, EmailStr
#
#
# class User(BaseModel):
#     id: int
#     name: str
#     email: EmailStr  # invalid emails get a 422 response automatically
#
#
# @app.post("/api/user")
# def create_user(user: User) -> dict[str, str]:
#     return {"message": f"Hello {user.name} (ID {user.id}), we'll email you at {user.email}."}


# Tutor profile management: readable validation messages and the five CRUD routes.
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.include_router(tutors.router)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# dist/ only exists after `npm run build`; in dev the Vite server serves the UI.
if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)
"""Password hashing, JWT access tokens and refresh-token values.

Passwords: HMAC-SHA256(pepper, password) is hashed with Argon2id. The pepper
lives only in an environment variable, so a stolen database alone is not
enough to start guessing passwords.

Access tokens: short-lived JWTs (HS256) carrying the user id ("sub"), the
security role ("role") and the session id ("sid").

Refresh tokens: random 256-bit strings. Only their SHA-256 hash is stored.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta
from functools import lru_cache
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from peerora.config import (
    JWT_ALGORITHM,
    JWT_ISSUER,
    get_access_token_minutes,
    get_jwt_secret,
    get_password_pepper,
)
from peerora.core.timeutils import utcnow

ACCESS_TOKEN_TYPE = "access"

# argon2-cffi defaults to Argon2id with sensible memory and time costs.
_password_hasher = PasswordHasher()


class InvalidTokenError(Exception):
    """The access token is missing, malformed, tampered with or expired."""


# ---- Passwords ----

def _pepper(password: str) -> str:
    return hmac.new(
        get_password_pepper().encode(), password.encode(), hashlib.sha256
    ).hexdigest()


def hash_password(password: str) -> str:
    return _password_hasher.hash(_pepper(password))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, _pepper(password))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _password_hasher.check_needs_rehash(password_hash)


@lru_cache
def _dummy_hash() -> str:
    return hash_password("not-a-real-password")


def burn_password_check_time(password: str) -> None:
    """Run one hash check for an unknown email, so a failed login takes about
    the same time whether or not the account exists."""
    verify_password(password, _dummy_hash())


# ---- Access tokens (JWT) ----

def create_access_token(
    user_id: int, role: str, session_id: str, lifetime: timedelta | None = None
) -> str:
    now = utcnow()
    if lifetime is None:
        lifetime = timedelta(minutes=get_access_token_minutes())
    payload = {
        "sub": str(user_id),
        "role": role,
        "sid": session_id,
        "type": ACCESS_TOKEN_TYPE,
        "iss": JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Verify signature, expiry, issuer and required claims, or raise InvalidTokenError."""
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],  # never accept "none" or another algorithm
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "sid", "role", "type"]},
        )
    except jwt.PyJWTError as error:
        raise InvalidTokenError from error
    if payload.get("type") != ACCESS_TOKEN_TYPE or not str(payload["sub"]).isdigit():
        raise InvalidTokenError
    return payload


# ---- Refresh tokens ----

def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

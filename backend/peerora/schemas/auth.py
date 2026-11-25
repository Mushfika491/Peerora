"""Signup, login and token schemas.

SignupIn has no "role" field and forbids unknown fields, so a visitor can
never register as an administrator: everyone who signs up gets role "user".
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from peerora.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    USER_FULL_NAME_MAX_LENGTH,
    USER_FULL_NAME_MIN_LENGTH,
)
from peerora.schemas.common import check_password_strength, normalize_email
from peerora.schemas.user import UserOut


class SignupIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    full_name: str = Field(min_length=USER_FULL_NAME_MIN_LENGTH, max_length=USER_FULL_NAME_MAX_LENGTH)
    email: EmailStr = Field(max_length=EMAIL_MAX_LENGTH)
    password: str
    # Only the two public account types. "admin" is not an account type.
    account_type: Literal["student", "tutor"]

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str, info) -> str:
        check_password_strength(value)
        email = info.data.get("email")
        if email and value.strip().lower() == email:
            raise ValueError("must not be the same as your email address")
        return value


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=1, max_length=EMAIL_MAX_LENGTH)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str) -> str:
        return normalize_email(value)


class TokenOut(BaseModel):
    """Returned by signup, login and refresh. The refresh token itself is
    never in the body: it is set as an HttpOnly cookie."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # seconds
    user: UserOut


class PasswordResetRequestIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr = Field(max_length=EMAIL_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str) -> str:
        return normalize_email(value)


class PasswordResetConfirmIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # token_urlsafe(32) gives 43 characters; allow some slack, refuse junk.
    token: str = Field(min_length=20, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return check_password_strength(value)  # the same policy as signup


class PasswordResetAvailabilityOut(BaseModel):
    available: bool
    token_minutes: int


class MessageOut(BaseModel):
    detail: str

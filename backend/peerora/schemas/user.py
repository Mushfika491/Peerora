"""User, profile, password and session schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from peerora.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    USER_FULL_NAME_MAX_LENGTH,
    USER_FULL_NAME_MIN_LENGTH,
)
from peerora.schemas.common import check_password_strength, normalize_email


class UserOut(BaseModel):
    """A user as the user themself sees it. Never contains the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    account_type: Literal["student", "tutor"]
    role: Literal["user", "admin"]
    created_at: datetime
    has_tutor_profile: bool = False


class ProfileUpdateIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    full_name: str | None = Field(
        default=None, min_length=USER_FULL_NAME_MIN_LENGTH, max_length=USER_FULL_NAME_MAX_LENGTH
    )
    email: EmailStr | None = Field(default=None, max_length=EMAIL_MAX_LENGTH)
    # Required only when the email address changes.
    current_password: str | None = Field(default=None, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str | None) -> str | None:
        return None if value is None else normalize_email(value)


class PasswordChangeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return check_password_strength(value)


class SessionOut(BaseModel):
    id: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    is_current: bool = False

"""Shared schema pieces: pagination and reusable field validators."""

import re
from typing import Generic, TypeVar

from pydantic import BaseModel

from peerora.constants import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """One page of a list: the items plus what is needed to show pagination."""

    items: list[T]
    total: int
    page: int
    page_size: int


def check_password_strength(password: str) -> str:
    """Backend password rules (mirrored in frontend/src/utils/authValidation.ts)."""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"must be at most {PASSWORD_MAX_LENGTH} characters")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("must contain at least one letter and one number")
    return password


def normalize_email(email: str) -> str:
    return email.strip().lower()

"""Pydantic schemas: the shape and validation rules of requests and responses.

TutorIn  - what the frontend sends for POST and PUT (validated here).
TutorOut - what the API returns (numbers are sent as JSON numbers).
The rules mirror frontend/src/utils/validation.ts.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from peerora.constants import (
    BIO_MAX_LENGTH,
    CGPA_MAX,
    CGPA_MIN,
    DEPARTMENTS,
    FULL_NAME_MAX_LENGTH,
    FULL_NAME_MIN_LENGTH,
    HEADLINE_MAX_LENGTH,
    PROFILE_IMAGE_URL_MAX_LENGTH,
    SEMESTER_MAX,
    SEMESTER_MIN,
    STUDENT_ID_LENGTH,
    SUBJECTS,
    TEACHING_MODES,
    TUTORING_EXPERIENCES,
)

IMAGE_URL_MESSAGE = "must be a valid web address starting with http:// or https://"


class TutorIn(BaseModel):
    # Spaces around text are removed before any length rule is checked.
    # Unknown fields are rejected so typos in a request cannot go unnoticed.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    full_name: str = Field(
        min_length=FULL_NAME_MIN_LENGTH, max_length=FULL_NAME_MAX_LENGTH
    )
    # Exactly 7 characters. Only the length is checked, nothing else.
    student_id: str = Field(min_length=STUDENT_ID_LENGTH, max_length=STUDENT_ID_LENGTH)
    department: str
    semester: int = Field(ge=SEMESTER_MIN, le=SEMESTER_MAX)
    cgpa: Decimal = Field(ge=CGPA_MIN, le=CGPA_MAX, decimal_places=2)
    headline: str = Field(min_length=1, max_length=HEADLINE_MAX_LENGTH)
    bio: str = Field(min_length=1, max_length=BIO_MAX_LENGTH)
    subjects: list[str] = Field(min_length=1)
    teaching_mode: str
    # Optional, never negative, at most 2 decimals. NUMERIC(12,2) allows up to
    # 10 digits before the decimal point, which is the only upper limit.
    hourly_rate: (
        Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)] | None
    ) = None
    tutoring_experience: str
    profile_image_url: (
        Annotated[str, Field(max_length=PROFILE_IMAGE_URL_MAX_LENGTH)] | None
    ) = None

    @field_validator("department")
    @classmethod
    def department_must_be_listed(cls, value: str) -> str:
        if value not in DEPARTMENTS:
            raise ValueError("must be one of the listed departments")
        return value

    @field_validator("subjects")
    @classmethod
    def subjects_must_be_valid(cls, value: list[str]) -> list[str]:
        if any(subject not in SUBJECTS for subject in value):
            raise ValueError("contains a subject that is not in the allowed list")
        if len(set(value)) != len(value):
            raise ValueError("contains the same subject more than once")
        return value

    @field_validator("teaching_mode")
    @classmethod
    def teaching_mode_must_be_allowed(cls, value: str) -> str:
        if value not in TEACHING_MODES:
            raise ValueError(f"must be one of: {', '.join(TEACHING_MODES)}")
        return value

    @field_validator("tutoring_experience")
    @classmethod
    def experience_must_be_allowed(cls, value: str) -> str:
        if value not in TUTORING_EXPERIENCES:
            raise ValueError(f"must be one of: {', '.join(TUTORING_EXPERIENCES)}")
        return value

    @field_validator("profile_image_url")
    @classmethod
    def image_url_must_be_web_address(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            parts = urlsplit(value)
        except ValueError:
            raise ValueError(IMAGE_URL_MESSAGE) from None
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise ValueError(IMAGE_URL_MESSAGE)
        return value


class TutorOut(BaseModel):
    # from_attributes lets Pydantic read a SQLAlchemy Tutor object directly.
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    student_id: str
    department: str
    semester: int
    cgpa: Decimal
    headline: str
    bio: str
    subjects: list[str]
    teaching_mode: str
    hourly_rate: Decimal | None
    tutoring_experience: str
    profile_image_url: str | None
    created_at: datetime
    updated_at: datetime

    # The database returns exact decimals. Pydantic would write them as text
    # ("3.75"), but the frontend requires JSON numbers (3.75).
    @field_serializer("cgpa")
    def cgpa_as_number(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("hourly_rate")
    def hourly_rate_as_number(self, value: Decimal | None) -> float | None:
        return None if value is None else float(value)
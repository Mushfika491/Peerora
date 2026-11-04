"""Readable validation error messages.

FastAPI's default messages do not name the field (for example "String should
have at most 100 characters"), and the frontend shows only the message text.
This handler keeps FastAPI's response shape, {"detail": [{"msg": ...}]}, but
writes a clear message that names the field.
"""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from peerora.constants import STUDENT_ID_LENGTH

FIELD_LABELS: dict[str, str] = {
    "full_name": "Full name",
    "student_id": "University Student ID",
    "department": "Department",
    "semester": "Semester",
    "cgpa": "CGPA",
    "headline": "Headline",
    "bio": "About Me",
    "subjects": "Subjects",
    "teaching_mode": "Teaching mode",
    "hourly_rate": "Hourly rate",
    "tutoring_experience": "Previous tutoring experience",
    "profile_image_url": "Profile picture URL",
    "tutor_id": "Tutor id",
}

# Same wording as the frontend validation messages.
RANGE_MESSAGES: dict[str, str] = {
    "semester": "Semester must be a whole number from 1 to 24.",
    "cgpa": "CGPA must be between 0.00 and 4.00.",
    "hourly_rate": "Hourly rate cannot be negative.",
}
NOT_A_NUMBER_MESSAGES: dict[str, str] = {
    "semester": "Semester must be a whole number from 1 to 24.",
    "cgpa": "CGPA must be a number (for example 3.75).",
    "hourly_rate": "Hourly rate must be a number (for example 500 or 500.50).",
}

RANGE_TYPES = {"greater_than_equal", "less_than_equal", "greater_than", "less_than"}
NOT_A_NUMBER_TYPES = {
    "int_parsing",
    "int_type",
    "int_from_float",
    "int_parsing_size",
    "decimal_parsing",
    "decimal_type",
    "finite_number",
}
TOO_MANY_DIGITS_TYPES = {"decimal_max_digits", "decimal_whole_digits"}


def _describe(field: str, error: dict[str, Any]) -> str:
    """Turn one Pydantic error into a sentence that names the field."""
    label = FIELD_LABELS.get(field) or ("Request body" if field == "" else field)
    error_type = str(error.get("type", ""))
    context = error.get("ctx") or {}
    message = str(error.get("msg", "Invalid value"))

    if error_type == "json_invalid":
        return "The request body is not valid JSON."
    if error_type == "missing":
        return f"{label} is required."
    if error_type == "extra_forbidden":
        return f"{label} is not an accepted field."
    if field == "tutor_id":
        return "Tutor id must be a positive whole number."
    if field == "student_id" and error_type in ("string_too_short", "string_too_long"):
        return f"{label} must be exactly {STUDENT_ID_LENGTH} characters."
    if error_type == "string_too_short":
        minimum = context.get("min_length", 1)
        if minimum == 1:
            return f"{label} is required."
        return f"{label} must be at least {minimum} characters."
    if error_type == "string_too_long":
        return f"{label} must be at most {context.get('max_length')} characters."
    if error_type == "too_short" and field == "subjects":
        return "Select at least one subject you can tutor."
    if error_type in RANGE_TYPES and field in RANGE_MESSAGES:
        return RANGE_MESSAGES[field]
    if error_type in NOT_A_NUMBER_TYPES and field in NOT_A_NUMBER_MESSAGES:
        return NOT_A_NUMBER_MESSAGES[field]
    if error_type == "decimal_max_places":
        return f"{label} can have at most {context.get('decimal_places')} decimal places."
    if error_type in TOO_MANY_DIGITS_TYPES:
        if field == "hourly_rate":
            return "Hourly rate is too large (the maximum is 9999999999.99 BDT)."
        return RANGE_MESSAGES.get(field, f"{label} is too large.")
    if error_type == "value_error":
        text = message.removeprefix("Value error, ").rstrip(".")
        return f"{label} {text}."
    return f"{label}: {message}"


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Replace FastAPI's default 422 response with readable messages."""
    details = []
    for error in exc.errors():
        location = list(error.get("loc", ()))
        # The first text after "body" or "path" is the field name.
        field = next((part for part in location[1:] if isinstance(part, str)), "")
        details.append(
            {
                "loc": location,
                "msg": _describe(field, error),
                "type": str(error.get("type", "")),
            }
        )
    return JSONResponse(status_code=422, content={"detail": details})
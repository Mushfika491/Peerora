"""Study record schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from peerora.constants import RECORD_CONTENT_MAX_LENGTH, RECORD_TITLE_MAX_LENGTH

RecordStatus = Literal["todo", "in_progress", "done"]


class RecordIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=RECORD_TITLE_MAX_LENGTH)
    content: str | None = Field(default=None, max_length=RECORD_CONTENT_MAX_LENGTH)
    status: RecordStatus = "todo"
    due_date: date | None = None
    assigned_to_id: int | None = Field(default=None, ge=1)


class RecordUpdate(BaseModel):
    """Partial update. Send only the fields that change."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=RECORD_TITLE_MAX_LENGTH)
    content: str | None = Field(default=None, max_length=RECORD_CONTENT_MAX_LENGTH)
    status: RecordStatus | None = None
    due_date: date | None = None
    assigned_to_id: int | None = Field(default=None, ge=1)


class RecordOut(BaseModel):
    id: int
    title: str
    content: str | None
    status: RecordStatus
    due_date: date | None
    group_id: int | None
    group_name: str | None
    created_by_id: int
    created_by_name: str
    assigned_to_id: int | None
    assigned_to_name: str | None
    created_at: datetime
    updated_at: datetime
    # What the current user may do (the backend still checks on every request).
    can_edit: bool
    can_assign: bool
    can_delete: bool

"""Study group and membership schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from peerora.constants import (
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_NAME_MIN_LENGTH,
)


class GroupIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=GROUP_NAME_MIN_LENGTH, max_length=GROUP_NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=GROUP_DESCRIPTION_MAX_LENGTH)
    subject: str | None = Field(default=None, max_length=100)


class GroupUpdate(BaseModel):
    """Partial update: only the fields that are sent are changed."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str | None = Field(default=None, min_length=GROUP_NAME_MIN_LENGTH, max_length=GROUP_NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=GROUP_DESCRIPTION_MAX_LENGTH)
    subject: str | None = Field(default=None, max_length=100)


GroupRole = Literal["owner", "editor", "viewer", "member"]


class GroupPermissions(BaseModel):
    """What a member may do with shared records (the owner may always do all three)."""

    can_create_records: bool
    can_update_records: bool
    can_assign_records: bool


class GroupOut(BaseModel):
    id: int
    name: str
    description: str | None
    subject: str | None
    owner_id: int
    owner_name: str
    my_role: GroupRole
    my_permissions: GroupPermissions
    member_count: int
    created_at: datetime
    updated_at: datetime


class MemberAddIn(BaseModel):
    """Add a member with a preset (editor = all permissions, viewer = none).
    Any permission sent explicitly overrides the preset."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    # "owner" cannot be given: each group has exactly one owner.
    group_role: Literal["editor", "viewer"] = "viewer"
    can_create_records: bool | None = None
    can_update_records: bool | None = None
    can_assign_records: bool | None = None


class MemberUpdateIn(BaseModel):
    """Change a member's permissions: a preset, individual permissions, or both
    (the preset is applied first, then the individual values)."""

    model_config = ConfigDict(extra="forbid")

    group_role: Literal["editor", "viewer"] | None = None
    can_create_records: bool | None = None
    can_update_records: bool | None = None
    can_assign_records: bool | None = None

    @model_validator(mode="after")
    def something_to_change(self) -> "MemberUpdateIn":
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("Send a group_role preset or at least one permission to change.")
        return self


class MemberOut(BaseModel):
    user_id: int
    full_name: str
    email: str
    group_role: GroupRole
    can_create_records: bool
    can_update_records: bool
    can_assign_records: bool
    joined_at: datetime

"""Schemas used only by the admin endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from peerora.constants import BAN_REASON_MAX_LENGTH
from peerora.schemas.group import MemberOut
from peerora.schemas.user import SessionOut


class OverviewOut(BaseModel):
    total_users: int
    banned_users: int
    admin_users: int
    total_records: int
    total_groups: int
    total_tutor_profiles: int
    new_users_last_7_days: int


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    account_type: str
    role: str
    is_banned: bool
    ban_reason: str | None
    banned_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime


class AdminGroupSummary(BaseModel):
    id: int
    name: str
    group_role: str


class AdminRecordOut(BaseModel):
    id: int
    title: str
    status: str
    group_id: int | None
    group_name: str | None
    created_by_id: int
    created_by_name: str
    created_by_email: str
    assigned_to_name: str | None
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    actor_id: int | None
    actor_email: str | None = None
    target_user_id: int | None
    target_user_email: str | None = None
    target_type: str | None
    target_id: str | None
    details: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AdminUserDetail(BaseModel):
    user: AdminUserOut
    tutor_profile_id: int | None
    groups: list[AdminGroupSummary]
    records: list[AdminRecordOut]
    record_count: int
    active_sessions: list[SessionOut]
    recent_activity: list[AuditLogOut]


class AdminGroupOut(BaseModel):
    id: int
    name: str
    subject: str | None
    owner_id: int
    owner_name: str
    owner_email: str
    member_count: int
    record_count: int
    created_at: datetime


class AdminGroupDetail(AdminGroupOut):
    description: str | None
    members: list[MemberOut]


class BanIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    reason: str = Field(min_length=3, max_length=BAN_REASON_MAX_LENGTH)


class UnbanIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    # Required, like a ban reason, and stored in the audit log.
    reason: str = Field(min_length=3, max_length=BAN_REASON_MAX_LENGTH)


class RoleChangeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "admin"]


class BulkBanIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_ids: list[int] = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=3, max_length=BAN_REASON_MAX_LENGTH)


class BulkUnbanIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_ids: list[int] = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=3, max_length=BAN_REASON_MAX_LENGTH)


class BulkDeleteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: list[int] = Field(min_length=1, max_length=100)


class BulkResultItem(BaseModel):
    id: int
    result: Literal["done", "not_found", "skipped_self", "skipped_admin", "already_done"]


class BulkResult(BaseModel):
    results: list[BulkResultItem]
    done: int


class TutorOwnerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int | None = Field(ge=1)


class FailedLoginGroup(BaseModel):
    key: str
    failures: int
    last_attempt_at: datetime


class FailedLoginOut(BaseModel):
    email: str
    ip_address: str | None
    user_agent: str | None
    failure_reason: str | None
    created_at: datetime


class SecurityReport(BaseModel):
    hours: int
    total_failures: int
    by_ip: list[FailedLoginGroup]
    by_account: list[FailedLoginGroup]
    recent: list[FailedLoginOut]

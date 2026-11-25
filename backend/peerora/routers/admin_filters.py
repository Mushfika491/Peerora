"""Query-parameter parsing shared by the admin list endpoints and the CSV
exports, so an export uses exactly the same filters as the list on screen."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import Depends, Query

from peerora.core.dependencies import require_permission
from peerora.core.permissions import Permission
from peerora.models import User
from peerora.services.admin_service import AuditFilters, GroupFilters, RecordFilters, UserFilters

# Every admin route depends on this: 401 without a token, 403 for non-admins.
AdminUser = Annotated[User, Depends(require_permission(Permission.ADMIN_ACCESS))]

Page = Annotated[int, Query(ge=1, le=100000)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def user_filters(
    q: Annotated[str | None, Query(max_length=100)] = None,
    role: Literal["user", "admin"] | None = None,
    account_type: Literal["student", "tutor"] | None = None,
    status: Literal["active", "banned"] | None = None,
) -> UserFilters:
    return UserFilters(q=q, role=role, account_type=account_type, status=status)


def record_filters(
    q: Annotated[str | None, Query(max_length=100)] = None,
    status: Literal["todo", "in_progress", "done"] | None = None,
    group_id: Annotated[int | None, Query(ge=1)] = None,
    scope: Literal["personal", "group"] | None = None,
) -> RecordFilters:
    return RecordFilters(q=q, status=status, group_id=group_id, scope=scope)


def group_filters(q: Annotated[str | None, Query(max_length=100)] = None) -> GroupFilters:
    return GroupFilters(q=q)


def audit_filters(
    q: Annotated[str | None, Query(max_length=100)] = None,
    action: Annotated[str | None, Query(max_length=40)] = None,
    user_id: Annotated[int | None, Query(ge=1)] = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> AuditFilters:
    return AuditFilters(q=q, action=action, user_id=user_id, date_from=date_from, date_to=date_to)


UserFilterParams = Annotated[UserFilters, Depends(user_filters)]
RecordFilterParams = Annotated[RecordFilters, Depends(record_filters)]
GroupFilterParams = Annotated[GroupFilters, Depends(group_filters)]
AuditFilterParams = Annotated[AuditFilters, Depends(audit_filters)]

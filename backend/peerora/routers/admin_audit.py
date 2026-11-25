"""Admin: audit/activity log and failed-login monitoring."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from peerora.core.dependencies import DbSession, require_permission
from peerora.core.permissions import Permission
from peerora.models import User
from peerora.routers.admin_filters import AuditFilterParams, Page, PageSize
from peerora.schemas.admin import AuditLogOut, SecurityReport
from peerora.schemas.common import Page as PageOf
from peerora.services import admin_service
from peerora.services.audit_service import AuditAction

router = APIRouter(prefix="/api/admin", tags=["admin: audit"])

Auditor = Annotated[User, Depends(require_permission(Permission.AUDIT_READ))]


@router.get("/audit-logs", response_model=PageOf[AuditLogOut])
def list_audit_logs(_: Auditor, db: DbSession, filters: AuditFilterParams, page: Page = 1, page_size: PageSize = 25):
    items, total = admin_service.list_audit_logs(db, filters, page, page_size)
    return PageOf[AuditLogOut](items=items, total=total, page=page, page_size=page_size)


@router.get("/audit-actions")
def list_audit_actions(_: Auditor) -> list[str]:
    """The action names, for the audit-log filter dropdown."""
    return [action.value for action in AuditAction]


@router.get("/security/failed-logins", response_model=SecurityReport)
def failed_logins(_: Auditor, db: DbSession, hours: Annotated[int, Query(ge=1, le=720)] = 24):
    """Failed login attempts in the last N hours, grouped by IP address and by account."""
    return admin_service.security_report(db, hours)

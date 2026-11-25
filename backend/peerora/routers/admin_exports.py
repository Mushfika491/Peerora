"""Admin: CSV exports of users, records and the activity log.

Each export accepts the same filter parameters as the matching list endpoint
and is recorded in the audit log. Times are ISO 8601 in UTC (with "+00:00"),
so a spreadsheet can convert them to any timezone without ambiguity."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from peerora.core.dependencies import Client, DbSession, require_permission
from peerora.core.permissions import Permission
from peerora.core.timeutils import utcnow
from peerora.models import User
from peerora.routers.admin_filters import AuditFilterParams, RecordFilterParams, UserFilterParams
from peerora.services import admin_service
from peerora.services.audit_service import AuditAction, log_event
from peerora.services.export_service import MAX_EXPORT_ROWS, csv_rows

router = APIRouter(prefix="/api/admin/exports", tags=["admin: exports"])

Exporter = Annotated[User, Depends(require_permission(Permission.DATA_EXPORT))]


def _csv_response(name: str, header: list[str], rows: list[list]) -> StreamingResponse:
    filename = f"peerora-{name}-{utcnow():%Y%m%d-%H%M%S}.csv"
    return StreamingResponse(
        csv_rows(header, rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _audit_export(db, admin: User, client, kind: str, filters, count: int) -> None:
    filters_used = {key: str(value) for key, value in vars(filters).items() if value is not None}
    log_event(db, AuditAction.EXPORT, client, actor_id=admin.id, target_type="export", target_id=kind,
              details={"export": kind, "filters": filters_used, "rows": count})
    db.commit()


@router.get("/users.csv")
def export_users(admin: Exporter, db: DbSession, client: Client, filters: UserFilterParams):
    users = db.scalars(admin_service.user_query(filters).limit(MAX_EXPORT_ROWS)).all()
    rows = [
        [u.id, u.email, u.full_name, u.account_type, u.role, "banned" if u.is_banned else "active",
         u.ban_reason, u.created_at.isoformat(), u.last_login_at.isoformat() if u.last_login_at else ""]
        for u in users
    ]
    _audit_export(db, admin, client, "users", filters, len(rows))
    return _csv_response("users", ["id", "email", "full_name", "account_type", "role", "status",
                                   "ban_reason", "created_at_utc", "last_login_at_utc"], rows)


@router.get("/records.csv")
def export_records(admin: Exporter, db: DbSession, client: Client, filters: RecordFilterParams):
    records = db.scalars(admin_service.record_query(filters).limit(MAX_EXPORT_ROWS)).unique().all()
    rows = [
        [r.id, r.title, r.status, r.group_id or "", r.group.name if r.group else "personal",
         r.creator.email, r.assignee.email if r.assignee else "",
         r.due_date.isoformat() if r.due_date else "", r.created_at.isoformat()]
        for r in records
    ]
    _audit_export(db, admin, client, "records", filters, len(rows))
    return _csv_response("records", ["id", "title", "status", "group_id", "group", "created_by",
                                     "assigned_to", "due_date", "created_at_utc"], rows)


@router.get("/audit-logs.csv")
def export_audit_logs(admin: Exporter, db: DbSession, client: Client, filters: AuditFilterParams):
    logs = admin_service.to_audit_out(db, list(db.scalars(admin_service.audit_query(filters).limit(MAX_EXPORT_ROWS))))
    rows = [
        [log.id, log.created_at.isoformat(), log.action, log.actor_email or "", log.target_user_email or "",
         log.target_type or "", log.target_id or "", log.ip_address or "", log.user_agent or "",
         "" if log.details is None else json.dumps(log.details, default=str)]
        for log in logs
    ]
    _audit_export(db, admin, client, "audit_logs", filters, len(rows))
    return _csv_response("audit-logs", ["id", "created_at_utc", "action", "actor", "target_user",
                                        "target_type", "target_id", "ip_address", "user_agent", "details"], rows)

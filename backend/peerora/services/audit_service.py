"""Audit logging: one function to record an event, with secrets stripped."""

from enum import StrEnum
from typing import Any

from sqlalchemy.orm import Session

from peerora.core.request_info import ClientInfo
from peerora.models import AuditLog


class AuditAction(StrEnum):
    SIGNUP = "signup"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REUSE_DETECTED = "token_reuse_detected"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PROFILE_UPDATED = "profile_updated"
    SESSION_REVOKED = "session_revoked"
    ROLE_CHANGED = "role_changed"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    TUTOR_PROFILE_DELETED = "tutor_profile_deleted"
    TUTOR_PROFILE_MODERATED = "tutor_profile_moderated"
    TUTOR_OWNER_CHANGED = "tutor_owner_changed"
    GROUP_DELETED = "group_deleted"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    MEMBER_PERMISSIONS_CHANGED = "member_permissions_changed"
    RECORD_DELETED = "record_deleted"
    EXPORT = "export"


# Any detail key containing one of these words is never stored.
_SENSITIVE_WORDS = ("password", "token", "secret", "hash", "pepper", "cookie", "authorization")


def sanitize(details: dict[str, Any] | None) -> dict[str, Any] | None:
    if not details:
        return None
    clean: dict[str, Any] = {}
    for key, value in details.items():
        if any(word in key.lower() for word in _SENSITIVE_WORDS):
            continue
        clean[key] = sanitize(value) if isinstance(value, dict) else value
    return clean


def log_event(
    db: Session,
    action: AuditAction,
    client: ClientInfo | None = None,
    *,
    actor_id: int | None = None,
    target_user_id: int | None = None,
    target_type: str | None = None,
    target_id: object = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit row to the current transaction (the caller commits)."""
    entry = AuditLog(
        action=str(action),
        actor_id=actor_id,
        target_user_id=target_user_id,
        target_type=target_type,
        target_id=None if target_id is None else str(target_id),
        details=sanitize(details),
        ip_address=client.ip_address if client else None,
        user_agent=client.user_agent if client else None,
    )
    db.add(entry)
    return entry

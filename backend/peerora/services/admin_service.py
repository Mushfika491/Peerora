"""Administrator features: overview, user management, moderation, audit queries.

Rules enforced here (in addition to the ADMIN permission checks on the routes):
  - an administrator cannot change their own role;
  - an administrator cannot ban themself or another administrator;
  - banning revokes every session, and banned users are refused on their
    next request (see core/dependencies.get_current_user);
  - every change is written to the audit log.
The *_query functions are shared by the list pages and the CSV exports, so an
export always contains exactly what the filtered list shows.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.orm import Session, aliased

from peerora.constants import ACCOUNT_TYPE_TUTOR, ROLE_ADMIN
from peerora.core.request_info import ClientInfo
from peerora.core.timeutils import utcnow
from peerora.models import AuditLog, GroupMembership, LoginAttempt, StudyGroup, StudyRecord, Tutor, User, UserSession
from peerora.schemas.admin import (
    AdminGroupDetail,
    AdminGroupOut,
    AdminGroupSummary,
    AdminRecordOut,
    AdminUserDetail,
    AdminUserOut,
    AuditLogOut,
    BulkResult,
    BulkResultItem,
    FailedLoginGroup,
    FailedLoginOut,
    OverviewOut,
    SecurityReport,
)
from peerora.schemas.user import SessionOut
from peerora.services import group_service, session_service
from peerora.services.audit_service import AuditAction, log_event


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found.")


def _forbidden(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


def _count(db: Session, statement: Select) -> int:
    return db.scalar(select(func.count()).select_from(statement.subquery())) or 0


def _like(text: str) -> str:
    escaped = text.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


# ---- Overview ----

def overview(db: Session) -> OverviewOut:
    week_ago = utcnow() - timedelta(days=7)
    return OverviewOut(
        total_users=db.scalar(select(func.count(User.id))) or 0,
        banned_users=db.scalar(select(func.count(User.id)).where(User.is_banned.is_(True))) or 0,
        admin_users=db.scalar(select(func.count(User.id)).where(User.role == ROLE_ADMIN)) or 0,
        total_records=db.scalar(select(func.count(StudyRecord.id))) or 0,
        total_groups=db.scalar(select(func.count(StudyGroup.id))) or 0,
        total_tutor_profiles=db.scalar(select(func.count(Tutor.id))) or 0,
        new_users_last_7_days=db.scalar(select(func.count(User.id)).where(User.created_at >= week_ago)) or 0,
    )


# ---- Users ----

@dataclass
class UserFilters:
    q: str | None = None  # email or name contains
    role: str | None = None
    account_type: str | None = None
    status: str | None = None  # "active" or "banned"


def user_query(filters: UserFilters) -> Select:
    statement = select(User)
    if filters.q:
        pattern = _like(filters.q)
        statement = statement.where(
            or_(func.lower(User.email).like(pattern, escape="\\"),
                func.lower(User.full_name).like(pattern, escape="\\"))
        )
    if filters.role:
        statement = statement.where(User.role == filters.role)
    if filters.account_type:
        statement = statement.where(User.account_type == filters.account_type)
    if filters.status == "banned":
        statement = statement.where(User.is_banned.is_(True))
    elif filters.status == "active":
        statement = statement.where(User.is_banned.is_(False))
    return statement.order_by(User.created_at.desc(), User.id.desc())


def list_users(db: Session, filters: UserFilters, page: int, page_size: int) -> tuple[list[User], int]:
    statement = user_query(filters)
    users = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return list(users), _count(db, statement)


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise _not_found("User")
    return user


def _session_out(session: UserSession) -> SessionOut:
    return SessionOut(
        id=session.id, ip_address=session.ip_address, user_agent=session.user_agent,
        created_at=session.created_at, last_used_at=session.last_used_at, expires_at=session.expires_at,
    )


def user_detail(db: Session, user_id: int) -> AdminUserDetail:
    user = get_user_or_404(db, user_id)
    groups = db.execute(
        select(StudyGroup.id, StudyGroup.name, GroupMembership.group_role)
        .join(GroupMembership, GroupMembership.group_id == StudyGroup.id)
        .where(GroupMembership.user_id == user.id)
        .order_by(StudyGroup.name)
    ).all()
    records_statement = record_query(RecordFilters(created_by_id=user.id))
    records = db.scalars(records_statement.limit(20)).all()
    activity = audit_query(AuditFilters(user_id=user.id))
    tutor_id = db.scalar(select(Tutor.id).where(Tutor.user_id == user.id))
    return AdminUserDetail(
        user=AdminUserOut.model_validate(user),
        tutor_profile_id=tutor_id,
        groups=[AdminGroupSummary(id=g.id, name=g.name, group_role=g.group_role) for g in groups],
        records=[to_admin_record(r) for r in records],
        record_count=_count(db, records_statement),
        active_sessions=[_session_out(s) for s in session_service.list_active_sessions(db, user.id)],
        recent_activity=to_audit_out(db, db.scalars(activity.limit(20)).all()),
    )


def _check_can_ban(actor: User, target: User) -> None:
    if target.id == actor.id:
        raise _forbidden("You cannot ban your own account.")
    if target.role == ROLE_ADMIN:
        raise _forbidden("Administrators cannot be banned. Change their role first.")


def ban_user(db: Session, actor: User, user_id: int, reason: str, client: ClientInfo) -> User:
    target = get_user_or_404(db, user_id)
    _check_can_ban(actor, target)
    if target.is_banned:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user is already banned.")
    _apply_ban(db, actor, target, reason, client)
    db.commit()
    return target


def _apply_ban(db: Session, actor: User, target: User, reason: str, client: ClientInfo) -> None:
    target.is_banned = True
    target.ban_reason = reason
    target.banned_at = utcnow()
    target.banned_by_id = actor.id
    revoked = session_service.revoke_all_sessions(db, target.id, "banned")
    log_event(db, AuditAction.USER_BANNED, client, actor_id=actor.id, target_user_id=target.id,
              target_type="user", target_id=target.id,
              details={"reason": reason, "sessions_revoked": revoked})


def unban_user(db: Session, actor: User, user_id: int, reason: str, client: ClientInfo) -> User:
    target = get_user_or_404(db, user_id)
    if not target.is_banned:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user is not banned.")
    _apply_unban(db, actor, target, reason, client)
    db.commit()
    return target


def _apply_unban(db: Session, actor: User, target: User, reason: str, client: ClientInfo) -> None:
    previous_reason = target.ban_reason
    target.is_banned = False
    target.ban_reason = None
    target.banned_at = None
    target.banned_by_id = None
    log_event(db, AuditAction.USER_UNBANNED, client, actor_id=actor.id, target_user_id=target.id,
              target_type="user", target_id=target.id,
              details={"reason": reason, "previous_ban_reason": previous_reason})


def bulk_ban(db: Session, actor: User, user_ids: list[int], reason: str, client: ClientInfo) -> BulkResult:
    results: list[BulkResultItem] = []
    for user_id in dict.fromkeys(user_ids):  # removes duplicates, keeps order
        target = db.get(User, user_id)
        if target is None:
            results.append(BulkResultItem(id=user_id, result="not_found"))
        elif target.id == actor.id:
            results.append(BulkResultItem(id=user_id, result="skipped_self"))
        elif target.role == ROLE_ADMIN:
            results.append(BulkResultItem(id=user_id, result="skipped_admin"))
        elif target.is_banned:
            results.append(BulkResultItem(id=user_id, result="already_done"))
        else:
            _apply_ban(db, actor, target, reason, client)
            results.append(BulkResultItem(id=user_id, result="done"))
    db.commit()
    return BulkResult(results=results, done=sum(item.result == "done" for item in results))


def bulk_unban(db: Session, actor: User, user_ids: list[int], reason: str, client: ClientInfo) -> BulkResult:
    results: list[BulkResultItem] = []
    for user_id in dict.fromkeys(user_ids):
        target = db.get(User, user_id)
        if target is None:
            results.append(BulkResultItem(id=user_id, result="not_found"))
        elif not target.is_banned:
            results.append(BulkResultItem(id=user_id, result="already_done"))
        else:
            _apply_unban(db, actor, target, reason, client)
            results.append(BulkResultItem(id=user_id, result="done"))
    db.commit()
    return BulkResult(results=results, done=sum(item.result == "done" for item in results))


def change_role(db: Session, actor: User, user_id: int, role: str, client: ClientInfo) -> User:
    target = get_user_or_404(db, user_id)
    if target.id == actor.id:
        raise _forbidden("You cannot change your own role.")
    if target.role != role:
        old_role = target.role
        target.role = role
        # Existing access tokens carry the old role and are now refused, so the
        # user's next request refreshes and receives the new role.
        log_event(db, AuditAction.ROLE_CHANGED, client, actor_id=actor.id, target_user_id=target.id,
                  target_type="user", target_id=target.id, details={"from": old_role, "to": role})
        db.commit()
    return target


def revoke_user_session(db: Session, actor: User, user_id: int, session_id: str, client: ClientInfo) -> None:
    session = db.get(UserSession, session_id)
    if session is None or session.user_id != user_id or session.revoked_at is not None:
        raise _not_found("Session")
    session_service.revoke_session(session, "admin_revoked")
    log_event(db, AuditAction.SESSION_REVOKED, client, actor_id=actor.id, target_user_id=user_id,
              target_type="session", target_id=session_id, details={"by_admin": True})
    db.commit()


def revoke_all_user_sessions(db: Session, actor: User, user_id: int, client: ClientInfo) -> int:
    get_user_or_404(db, user_id)
    revoked = session_service.revoke_all_sessions(db, user_id, "admin_revoked")
    log_event(db, AuditAction.SESSION_REVOKED, client, actor_id=actor.id, target_user_id=user_id,
              target_type="user", target_id=user_id, details={"by_admin": True, "count": revoked})
    db.commit()
    return revoked


def set_tutor_owner(db: Session, actor: User, tutor_id: int, user_id: int | None, client: ClientInfo) -> Tutor:
    """Link a tutor profile (e.g. one created before accounts existed) to a tutor account."""
    tutor = db.get(Tutor, tutor_id)
    if tutor is None:
        raise _not_found("Tutor")
    if user_id is not None:
        owner = get_user_or_404(db, user_id)
        if owner.account_type != ACCOUNT_TYPE_TUTOR:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                detail="Only a tutor account can own a tutor profile.")
        existing = db.scalar(select(Tutor.id).where(Tutor.user_id == user_id, Tutor.id != tutor_id))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="This user already owns another tutor profile.")
    old_owner = tutor.user_id
    tutor.user_id = user_id
    log_event(db, AuditAction.TUTOR_OWNER_CHANGED, client, actor_id=actor.id, target_user_id=user_id,
              target_type="tutor", target_id=tutor.id, details={"from_user_id": old_owner, "to_user_id": user_id})
    db.commit()
    db.refresh(tutor)
    return tutor


# ---- Content moderation ----

@dataclass
class RecordFilters:
    q: str | None = None  # title or creator email contains
    status: str | None = None
    group_id: int | None = None
    scope: str | None = None  # "personal" or "group"
    created_by_id: int | None = None


_Creator = aliased(User)


def record_query(filters: RecordFilters) -> Select:
    statement = select(StudyRecord).join(_Creator, _Creator.id == StudyRecord.created_by_id)
    if filters.q:
        pattern = _like(filters.q)
        statement = statement.where(
            or_(func.lower(StudyRecord.title).like(pattern, escape="\\"),
                func.lower(_Creator.email).like(pattern, escape="\\"))
        )
    if filters.status:
        statement = statement.where(StudyRecord.status == filters.status)
    if filters.group_id is not None:
        statement = statement.where(StudyRecord.group_id == filters.group_id)
    if filters.scope == "personal":
        statement = statement.where(StudyRecord.group_id.is_(None))
    elif filters.scope == "group":
        statement = statement.where(StudyRecord.group_id.is_not(None))
    if filters.created_by_id is not None:
        statement = statement.where(StudyRecord.created_by_id == filters.created_by_id)
    return statement.order_by(StudyRecord.created_at.desc(), StudyRecord.id.desc())


def to_admin_record(record: StudyRecord) -> AdminRecordOut:
    return AdminRecordOut(
        id=record.id, title=record.title, status=record.status,
        group_id=record.group_id, group_name=record.group.name if record.group else None,
        created_by_id=record.created_by_id, created_by_name=record.creator.full_name,
        created_by_email=record.creator.email,
        assigned_to_name=record.assignee.full_name if record.assignee else None,
        created_at=record.created_at,
    )


def list_records(db: Session, filters: RecordFilters, page: int, page_size: int) -> tuple[list[AdminRecordOut], int]:
    statement = record_query(filters)
    records = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return [to_admin_record(r) for r in records], _count(db, statement)


def delete_records(db: Session, actor: User, ids: list[int], client: ClientInfo) -> BulkResult:
    results: list[BulkResultItem] = []
    for record_id in dict.fromkeys(ids):
        record = db.get(StudyRecord, record_id)
        if record is None:
            results.append(BulkResultItem(id=record_id, result="not_found"))
            continue
        log_event(db, AuditAction.RECORD_DELETED, client, actor_id=actor.id, target_user_id=record.created_by_id,
                  target_type="record", target_id=record.id,
                  details={"title": record.title, "group_id": record.group_id,
                           # True only when an admin removes someone else's record.
                           "by_admin": record.created_by_id != actor.id})
        db.delete(record)
        results.append(BulkResultItem(id=record_id, result="done"))
    db.commit()
    return BulkResult(results=results, done=sum(item.result == "done" for item in results))


@dataclass
class GroupFilters:
    q: str | None = None  # group name or owner email contains


_Owner = aliased(User)


def group_query(filters: GroupFilters) -> Select:
    statement = select(StudyGroup).join(_Owner, _Owner.id == StudyGroup.owner_id)
    if filters.q:
        pattern = _like(filters.q)
        statement = statement.where(
            or_(func.lower(StudyGroup.name).like(pattern, escape="\\"),
                func.lower(_Owner.email).like(pattern, escape="\\"))
        )
    return statement.order_by(StudyGroup.created_at.desc(), StudyGroup.id.desc())


def to_admin_group(db: Session, group: StudyGroup) -> AdminGroupOut:
    return AdminGroupOut(
        id=group.id, name=group.name, subject=group.subject,
        owner_id=group.owner_id, owner_name=group.owner.full_name, owner_email=group.owner.email,
        member_count=group_service.member_count(db, group.id),
        record_count=db.scalar(select(func.count(StudyRecord.id)).where(StudyRecord.group_id == group.id)) or 0,
        created_at=group.created_at,
    )


def list_groups(db: Session, filters: GroupFilters, page: int, page_size: int) -> tuple[list[AdminGroupOut], int]:
    statement = group_query(filters)
    groups = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return [to_admin_group(db, g) for g in groups], _count(db, statement)


def group_detail(db: Session, group_id: int) -> AdminGroupDetail:
    group = db.get(StudyGroup, group_id)
    if group is None:
        raise _not_found("Study group")
    summary = to_admin_group(db, group)
    return AdminGroupDetail(**summary.model_dump(), description=group.description,
                            members=group_service.list_members(db, group.id))


def delete_groups(db: Session, actor: User, ids: list[int], client: ClientInfo) -> BulkResult:
    results: list[BulkResultItem] = []
    for group_id in dict.fromkeys(ids):
        group = db.get(StudyGroup, group_id)
        if group is None:
            results.append(BulkResultItem(id=group_id, result="not_found"))
            continue
        log_event(db, AuditAction.GROUP_DELETED, client, actor_id=actor.id, target_user_id=group.owner_id,
                  target_type="group", target_id=group.id,
                  details={"name": group.name, "by_admin": group.owner_id != actor.id})
        db.delete(group)
        results.append(BulkResultItem(id=group_id, result="done"))
    db.commit()
    return BulkResult(results=results, done=sum(item.result == "done" for item in results))


# ---- Audit log and security monitoring ----

@dataclass
class AuditFilters:
    q: str | None = None  # action, IP, browser, details or user email contains
    action: str | None = None
    user_id: int | None = None  # actor or target
    date_from: datetime | None = None
    date_to: datetime | None = None


_Actor = aliased(User)
_Target = aliased(User)


def audit_query(filters: AuditFilters) -> Select:
    statement = select(AuditLog)
    if filters.q:
        # Text search covers the action, IP address, browser, the details, and
        # the email of the user who acted or was affected.
        pattern = _like(filters.q)
        statement = (
            statement.outerjoin(_Actor, _Actor.id == AuditLog.actor_id)
            .outerjoin(_Target, _Target.id == AuditLog.target_user_id)
            .where(
                or_(
                    func.lower(AuditLog.action).like(pattern, escape="\\"),
                    func.lower(AuditLog.ip_address).like(pattern, escape="\\"),
                    func.lower(AuditLog.user_agent).like(pattern, escape="\\"),
                    func.lower(cast(AuditLog.details, String)).like(pattern, escape="\\"),
                    func.lower(_Actor.email).like(pattern, escape="\\"),
                    func.lower(_Target.email).like(pattern, escape="\\"),
                )
            )
        )
    if filters.action:
        statement = statement.where(AuditLog.action == filters.action)
    if filters.user_id is not None:
        statement = statement.where(
            or_(AuditLog.actor_id == filters.user_id, AuditLog.target_user_id == filters.user_id)
        )
    if filters.date_from is not None:
        statement = statement.where(AuditLog.created_at >= filters.date_from)
    if filters.date_to is not None:
        statement = statement.where(AuditLog.created_at <= filters.date_to)
    return statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())


def to_audit_out(db: Session, logs: list[AuditLog]) -> list[AuditLogOut]:
    user_ids = {log.actor_id for log in logs} | {log.target_user_id for log in logs}
    user_ids.discard(None)
    emails = dict(db.execute(select(User.id, User.email).where(User.id.in_(user_ids))).all()) if user_ids else {}
    return [
        AuditLogOut.model_validate(log).model_copy(update={
            "actor_email": emails.get(log.actor_id),
            "target_user_email": emails.get(log.target_user_id),
        })
        for log in logs
    ]


def list_audit_logs(db: Session, filters: AuditFilters, page: int, page_size: int) -> tuple[list[AuditLogOut], int]:
    statement = audit_query(filters)
    logs = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return to_audit_out(db, list(logs)), _count(db, statement)


def security_report(db: Session, hours: int) -> SecurityReport:
    since = utcnow() - timedelta(hours=hours)
    failed = (LoginAttempt.success.is_(False), LoginAttempt.created_at >= since)

    def grouped(column) -> list[FailedLoginGroup]:
        rows = db.execute(
            select(column, func.count(LoginAttempt.id), func.max(LoginAttempt.created_at))
            .where(*failed, column.is_not(None))
            .group_by(column)
            .order_by(func.count(LoginAttempt.id).desc())
            .limit(20)
        ).all()
        return [FailedLoginGroup(key=key, failures=count, last_attempt_at=last) for key, count, last in rows]

    recent = db.scalars(
        select(LoginAttempt).where(*failed).order_by(LoginAttempt.created_at.desc()).limit(50)
    ).all()
    return SecurityReport(
        hours=hours,
        total_failures=db.scalar(select(func.count(LoginAttempt.id)).where(*failed)) or 0,
        by_ip=grouped(LoginAttempt.ip_address),
        by_account=grouped(LoginAttempt.email),
        recent=[
            FailedLoginOut(email=a.email, ip_address=a.ip_address, user_agent=a.user_agent,
                           failure_reason=a.failure_reason, created_at=a.created_at)
            for a in recent
        ],
    )

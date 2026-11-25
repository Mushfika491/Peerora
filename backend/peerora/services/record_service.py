"""Study records: personal records and shared group records.

Who may do what:
  personal record  -> only its creator (everyone else gets 404)
  group record     -> any member can read;
                      creating needs can_create_records,
                      editing needs can_update_records,
                      setting or changing the assignee needs can_assign_records;
                      the assignee may always change the status of their record;
                      the owner can delete any record, a member with
                      can_update_records only the records they created.
The owner holds every permission (see group_service.py).
"""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from peerora.core.request_info import ClientInfo
from peerora.models import GroupMembership, StudyRecord, User
from peerora.schemas.record import RecordIn, RecordOut, RecordUpdate
from peerora.services import group_service
from peerora.services.audit_service import AuditAction, log_event

RECORD_NOT_FOUND = "Record not found."


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=RECORD_NOT_FOUND)


def _forbidden(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


# ---- Permission rules (pure functions, easy to test and explain) ----

def can_edit(record: StudyRecord, user: User, membership: GroupMembership | None) -> bool:
    if record.group_id is None:
        return record.created_by_id == user.id
    return group_service.can_update(membership)


def can_assign(record: StudyRecord, user: User, membership: GroupMembership | None) -> bool:
    if record.group_id is None:
        return record.created_by_id == user.id  # (personal records: only to yourself)
    return group_service.can_assign(membership)


def can_delete(record: StudyRecord, user: User, membership: GroupMembership | None) -> bool:
    if record.group_id is None:
        return record.created_by_id == user.id
    if group_service.is_owner(membership):
        return True
    return group_service.can_update(membership) and record.created_by_id == user.id


def to_record_out(record: StudyRecord, user: User, membership: GroupMembership | None) -> RecordOut:
    return RecordOut(
        id=record.id,
        title=record.title,
        content=record.content,
        status=record.status,
        due_date=record.due_date,
        group_id=record.group_id,
        group_name=record.group.name if record.group else None,
        created_by_id=record.created_by_id,
        created_by_name=record.creator.full_name,
        assigned_to_id=record.assigned_to_id,
        assigned_to_name=record.assignee.full_name if record.assignee else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
        can_edit=can_edit(record, user, membership),
        can_assign=can_assign(record, user, membership),
        can_delete=can_delete(record, user, membership),
    )


def _check_assignee(db: Session, group_id: int | None, user: User, assigned_to_id: int | None) -> None:
    if assigned_to_id is None:
        return
    if group_id is None:
        if assigned_to_id != user.id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                detail="A personal record can only be assigned to yourself.")
        return
    if group_service.get_membership(db, group_id, assigned_to_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Records can only be assigned to members of this group.")


def load_for_user(db: Session, record_id: int, user: User) -> tuple[StudyRecord, GroupMembership | None]:
    """The record plus the caller's group membership. 404 when the caller may not see it."""
    record = db.get(StudyRecord, record_id)
    if record is None:
        raise _not_found()
    if record.group_id is None:
        if record.created_by_id != user.id:
            raise _not_found()
        return record, None
    membership = group_service.get_membership(db, record.group_id, user.id)
    if membership is None:
        raise _not_found()
    return record, membership


# ---- Queries ----

def list_personal(db: Session, user: User) -> list[RecordOut]:
    records = db.scalars(
        select(StudyRecord)
        .where(StudyRecord.group_id.is_(None), StudyRecord.created_by_id == user.id)
        .order_by(StudyRecord.updated_at.desc())
    ).all()
    return [to_record_out(r, user, None) for r in records]


def list_assigned(db: Session, user: User) -> list[RecordOut]:
    """Group records assigned to the user, in groups they still belong to."""
    rows = db.execute(
        select(StudyRecord, GroupMembership)
        .join(GroupMembership, (GroupMembership.group_id == StudyRecord.group_id)
              & (GroupMembership.user_id == user.id))
        .where(StudyRecord.assigned_to_id == user.id)
        .order_by(StudyRecord.updated_at.desc())
    ).all()
    return [to_record_out(r, user, m) for r, m in rows]


def list_group_records(db: Session, user: User, group_id: int) -> list[RecordOut]:
    _, membership = group_service.load_for_member(db, group_id, user)
    records = db.scalars(
        select(StudyRecord).where(StudyRecord.group_id == group_id).order_by(StudyRecord.updated_at.desc())
    ).all()
    return [to_record_out(r, user, membership) for r in records]


def visible_records_query(user: User):
    """Every record the user may see (used by the dashboard)."""
    member_groups = select(GroupMembership.group_id).where(GroupMembership.user_id == user.id)
    return select(StudyRecord).where(
        or_(
            (StudyRecord.group_id.is_(None)) & (StudyRecord.created_by_id == user.id),
            StudyRecord.group_id.in_(member_groups),
        )
    )


# ---- Changes ----

def create_personal(db: Session, user: User, data: RecordIn) -> RecordOut:
    _check_assignee(db, None, user, data.assigned_to_id)
    record = StudyRecord(**data.model_dump(), created_by_id=user.id, group_id=None)
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_record_out(record, user, None)


def create_in_group(db: Session, user: User, group_id: int, data: RecordIn) -> RecordOut:
    _, membership = group_service.load_for_member(db, group_id, user)
    if not group_service.can_create(membership):
        raise _forbidden("You do not have permission to create records in this group.")
    if data.assigned_to_id is not None and not group_service.can_assign(membership):
        raise _forbidden("You do not have permission to assign records in this group.")
    _check_assignee(db, group_id, user, data.assigned_to_id)
    record = StudyRecord(**data.model_dump(), created_by_id=user.id, group_id=group_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_record_out(record, user, membership)


def update_record(db: Session, user: User, record_id: int, data: RecordUpdate) -> RecordOut:
    record, membership = load_for_user(db, record_id, user)
    changes = data.model_dump(exclude_unset=True)
    # Sending the current assignee again is not a change and needs no permission.
    if changes.get("assigned_to_id", record.assigned_to_id) == record.assigned_to_id:
        changes.pop("assigned_to_id", None)

    content_changes = set(changes) - {"assigned_to_id"}
    if content_changes and not can_edit(record, user, membership):
        # The assignee may always move their own task forward (status only).
        if not (content_changes <= {"status"} and record.assigned_to_id == user.id):
            raise _forbidden("You do not have permission to edit this record.")
    if "assigned_to_id" in changes:
        if not can_assign(record, user, membership):
            raise _forbidden("You do not have permission to assign records in this group.")
        _check_assignee(db, record.group_id, user, changes["assigned_to_id"])
    for field, value in changes.items():
        if field in ("title", "status") and value is None:
            continue  # required fields cannot be cleared
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return to_record_out(record, user, membership)


def delete_record(db: Session, user: User, record_id: int, client: ClientInfo) -> None:
    record, membership = load_for_user(db, record_id, user)
    if not can_delete(record, user, membership):
        raise _forbidden("You do not have permission to delete this record.")
    log_event(db, AuditAction.RECORD_DELETED, client, actor_id=user.id, target_user_id=record.created_by_id,
              target_type="record", target_id=record.id,
              details={"title": record.title, "group_id": record.group_id})
    db.delete(record)
    db.commit()


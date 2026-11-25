"""Study groups and memberships.

Permission model (enforced here and in record_service.py, never only in the UI):
  non-member -> 404 for everything (the group's existence is not revealed)
  any member -> read the group, its members and its records
  each non-owner member has three independent permissions:
      can_create_records  - add shared records
      can_update_records  - edit shared records
      can_assign_records  - choose who a record is assigned to
  owner      -> every permission, plus rename/update/delete the group and
                manage members and their permissions (owner only)
The role label is derived from the permissions: editor = all three,
viewer = none, member = any other mix. Members may leave; the owner cannot
leave (they delete the group instead).
"""

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from peerora.constants import (
    GROUP_PERMISSION_FIELDS,
    GROUP_ROLE_MEMBER,
    GROUP_ROLE_OWNER,
    GROUP_ROLE_PRESETS,
    GROUP_ROLE_VIEWER,
)
from peerora.core.request_info import ClientInfo
from peerora.models import GroupMembership, StudyGroup, StudyRecord, User
from peerora.schemas.group import GroupIn, GroupOut, GroupPermissions, GroupUpdate, MemberOut
from peerora.services.audit_service import AuditAction, log_event

GROUP_NOT_FOUND = "Study group not found."


def _forbidden(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


# ---- Permission helpers (pure functions, easy to test and explain) ----

def is_owner(membership: GroupMembership | None) -> bool:
    return membership is not None and membership.group_role == GROUP_ROLE_OWNER


def can_create(membership: GroupMembership | None) -> bool:
    return is_owner(membership) or (membership is not None and membership.can_create_records)


def can_update(membership: GroupMembership | None) -> bool:
    return is_owner(membership) or (membership is not None and membership.can_update_records)


def can_assign(membership: GroupMembership | None) -> bool:
    return is_owner(membership) or (membership is not None and membership.can_assign_records)


def derive_role(create: bool, update: bool, assign: bool) -> str:
    """The label shown for a non-owner member's permission combination."""
    for role, preset in GROUP_ROLE_PRESETS.items():
        if (create, update, assign) == preset:
            return role
    return GROUP_ROLE_MEMBER


def apply_permissions(membership: GroupMembership, preset: str | None, overrides: dict[str, bool | None]) -> None:
    """Set a non-owner's permissions: preset first, then explicit values, then the label."""
    if preset is not None:
        for field, value in zip(GROUP_PERMISSION_FIELDS, GROUP_ROLE_PRESETS[preset]):
            setattr(membership, field, value)
    for field in GROUP_PERMISSION_FIELDS:
        if overrides.get(field) is not None:
            setattr(membership, field, overrides[field])
    membership.group_role = derive_role(
        membership.can_create_records, membership.can_update_records, membership.can_assign_records
    )


def permissions_of(membership: GroupMembership) -> GroupPermissions:
    return GroupPermissions(
        can_create_records=can_create(membership),
        can_update_records=can_update(membership),
        can_assign_records=can_assign(membership),
    )


# ---- Loading ----

def get_membership(db: Session, group_id: int, user_id: int) -> GroupMembership | None:
    return db.scalar(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
        )
    )


def load_for_member(db: Session, group_id: int, user: User) -> tuple[StudyGroup, GroupMembership]:
    """The group plus the caller's membership, or 404 when the caller is not a member."""
    group = db.get(StudyGroup, group_id)
    membership = get_membership(db, group_id, user.id) if group else None
    if group is None or membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GROUP_NOT_FOUND)
    return group, membership


def require_owner(membership: GroupMembership) -> None:
    if not is_owner(membership):
        raise _forbidden("Only the group owner can do this.")


def member_count(db: Session, group_id: int) -> int:
    return db.scalar(
        select(func.count(GroupMembership.id)).where(GroupMembership.group_id == group_id)
    ) or 0


def to_group_out(db: Session, group: StudyGroup, membership: GroupMembership) -> GroupOut:
    return GroupOut(
        id=group.id,
        name=group.name,
        description=group.description,
        subject=group.subject,
        owner_id=group.owner_id,
        owner_name=group.owner.full_name,
        my_role=membership.group_role,
        my_permissions=permissions_of(membership),
        member_count=member_count(db, group.id),
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


def to_member_out(membership: GroupMembership) -> MemberOut:
    permissions = permissions_of(membership)
    return MemberOut(
        user_id=membership.user_id,
        full_name=membership.user.full_name,
        email=membership.user.email,
        group_role=membership.group_role,
        can_create_records=permissions.can_create_records,
        can_update_records=permissions.can_update_records,
        can_assign_records=permissions.can_assign_records,
        joined_at=membership.joined_at,
    )


def list_my_groups(db: Session, user: User) -> list[GroupOut]:
    rows = db.execute(
        select(StudyGroup, GroupMembership)
        .join(GroupMembership, GroupMembership.group_id == StudyGroup.id)
        .where(GroupMembership.user_id == user.id)
        .order_by(StudyGroup.updated_at.desc())
    ).all()
    return [to_group_out(db, group, membership) for group, membership in rows]


# ---- Group changes ----

def create_group(db: Session, user: User, data: GroupIn) -> GroupOut:
    group = StudyGroup(**data.model_dump(), owner_id=user.id)
    db.add(group)
    db.flush()
    membership = GroupMembership(
        group_id=group.id, user_id=user.id, group_role=GROUP_ROLE_OWNER, added_by_id=user.id,
        can_create_records=True, can_update_records=True, can_assign_records=True,
    )
    db.add(membership)
    db.commit()
    db.refresh(group)
    return to_group_out(db, group, membership)


def update_group(db: Session, user: User, group_id: int, data: GroupUpdate) -> GroupOut:
    group, membership = load_for_member(db, group_id, user)
    require_owner(membership)
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "name" and value is None:
            continue  # the name cannot be removed
        setattr(group, field, value)
    db.commit()
    db.refresh(group)
    return to_group_out(db, group, membership)


def delete_group(db: Session, group: StudyGroup, actor: User, client: ClientInfo, *, by_admin: bool = False) -> None:
    log_event(db, AuditAction.GROUP_DELETED, client, actor_id=actor.id, target_user_id=group.owner_id,
              target_type="group", target_id=group.id,
              details={"name": group.name, "by_admin": by_admin})
    db.delete(group)  # memberships and records are removed by ON DELETE CASCADE
    db.commit()


# ---- Membership changes (owner only, except leaving) ----

def list_members(db: Session, group_id: int) -> list[MemberOut]:
    memberships = db.scalars(
        select(GroupMembership)
        .where(GroupMembership.group_id == group_id)
        .order_by(GroupMembership.joined_at, GroupMembership.id)
    ).all()
    return [to_member_out(m) for m in memberships]


def add_member(
    db: Session, owner: User, group_id: int, email: str, preset: str,
    overrides: dict[str, bool | None], client: ClientInfo,
) -> MemberOut:
    _, membership = load_for_member(db, group_id, owner)
    require_owner(membership)
    target = db.scalar(select(User).where(User.email == email.lower()))
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user with this email address was found.")
    if target.is_banned:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This account is suspended and cannot be added.")
    if get_membership(db, group_id, target.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user is already a member of the group.")
    new = GroupMembership(group_id=group_id, user_id=target.id, group_role=GROUP_ROLE_VIEWER, added_by_id=owner.id)
    apply_permissions(new, preset, overrides)
    db.add(new)
    log_event(db, AuditAction.MEMBER_ADDED, client, actor_id=owner.id, target_user_id=target.id,
              target_type="group", target_id=group_id,
              details={"group_role": new.group_role, **{f: getattr(new, f) for f in GROUP_PERMISSION_FIELDS}})
    db.commit()
    db.refresh(new)
    return to_member_out(new)


def update_member(
    db: Session, owner: User, group_id: int, user_id: int, preset: str | None,
    overrides: dict[str, bool | None], client: ClientInfo,
) -> MemberOut:
    _, membership = load_for_member(db, group_id, owner)
    require_owner(membership)
    target = get_membership(db, group_id, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    if is_owner(target):
        raise _forbidden("The owner's role and permissions cannot be changed.")
    before = {f: getattr(target, f) for f in GROUP_PERMISSION_FIELDS}
    apply_permissions(target, preset, overrides)
    after = {f: getattr(target, f) for f in GROUP_PERMISSION_FIELDS}
    if after != before:
        log_event(db, AuditAction.MEMBER_PERMISSIONS_CHANGED, client, actor_id=owner.id, target_user_id=user_id,
                  target_type="group", target_id=group_id,
                  details={"from": before, "to": after, "group_role": target.group_role})
    db.commit()
    return to_member_out(target)


def remove_member(db: Session, actor: User, group_id: int, user_id: int, client: ClientInfo) -> None:
    """The owner removes a member, or a member removes themself (leaves)."""
    _, membership = load_for_member(db, group_id, actor)
    leaving = user_id == actor.id
    if leaving:
        if is_owner(membership):
            raise _forbidden("The owner cannot leave the group. Delete the group instead.")
        target = membership
    else:
        require_owner(membership)
        target = get_membership(db, group_id, user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    # Records assigned to the departing member become unassigned.
    db.execute(
        update(StudyRecord)
        .where(StudyRecord.group_id == group_id, StudyRecord.assigned_to_id == user_id)
        .values(assigned_to_id=None)
    )
    db.delete(target)
    log_event(db, AuditAction.MEMBER_REMOVED, client, actor_id=actor.id, target_user_id=user_id,
              target_type="group", target_id=group_id, details={"left": leaving})
    db.commit()


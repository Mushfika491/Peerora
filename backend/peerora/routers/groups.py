"""Study group endpoints. All rules live in services/group_service.py and
services/record_service.py; every route requires a signed-in user."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from peerora.core.dependencies import Client, CurrentUser, DbSession, require_permission
from peerora.core.permissions import Permission
from peerora.models import User
from peerora.constants import GROUP_PERMISSION_FIELDS
from peerora.schemas.group import GroupIn, GroupOut, GroupUpdate, MemberAddIn, MemberOut, MemberUpdateIn
from peerora.schemas.record import RecordIn, RecordOut
from peerora.services import group_service, record_service

router = APIRouter(prefix="/api/groups", tags=["study groups"])

GroupId = Annotated[int, Path(ge=1, le=2147483647)]
UserId = Annotated[int, Path(ge=1, le=2147483647)]
GroupCreator = Annotated[User, Depends(require_permission(Permission.GROUP_CREATE))]


@router.get("", response_model=list[GroupOut])
def list_my_groups(user: CurrentUser, db: DbSession):
    """Groups the current user belongs to (as owner, editor or viewer)."""
    return group_service.list_my_groups(db, user)


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(data: GroupIn, user: GroupCreator, db: DbSession):
    """The creator becomes the group owner."""
    return group_service.create_group(db, user, data)


@router.get("/{group_id}", response_model=GroupOut)
def read_group(group_id: GroupId, user: CurrentUser, db: DbSession):
    group, membership = group_service.load_for_member(db, group_id, user)
    return group_service.to_group_out(db, group, membership)


@router.patch("/{group_id}", response_model=GroupOut)
def update_group(group_id: GroupId, data: GroupUpdate, user: CurrentUser, db: DbSession):
    """Owner only: rename or edit the group."""
    return group_service.update_group(db, user, group_id, data)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: GroupId, user: CurrentUser, db: DbSession, client: Client):
    """Owner only. Also deletes the group's memberships and records."""
    group, membership = group_service.load_for_member(db, group_id, user)
    group_service.require_owner(membership)
    group_service.delete_group(db, group, user, client)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{group_id}/members", response_model=list[MemberOut])
def list_members(group_id: GroupId, user: CurrentUser, db: DbSession):
    group_service.load_for_member(db, group_id, user)
    return group_service.list_members(db, group_id)


@router.post("/{group_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(group_id: GroupId, data: MemberAddIn, user: CurrentUser, db: DbSession, client: Client):
    """Owner only: add an existing user by email. group_role is a preset
    (editor = all permissions, viewer = none); explicit can_* values override it."""
    overrides = {field: getattr(data, field) for field in GROUP_PERMISSION_FIELDS}
    return group_service.add_member(db, user, group_id, data.email, data.group_role, overrides, client)


@router.patch("/{group_id}/members/{user_id}", response_model=MemberOut)
def update_member(
    group_id: GroupId, user_id: UserId, data: MemberUpdateIn, user: CurrentUser, db: DbSession, client: Client
):
    """Owner only: change a member's create / update / assign permissions,
    by preset (group_role) and/or individually. The role label is derived."""
    overrides = {field: getattr(data, field) for field in GROUP_PERMISSION_FIELDS}
    return group_service.update_member(db, user, group_id, user_id, data.group_role, overrides, client)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(group_id: GroupId, user_id: UserId, user: CurrentUser, db: DbSession, client: Client):
    """The owner removes a member, or a member removes themself (leaves)."""
    group_service.remove_member(db, user, group_id, user_id, client)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{group_id}/records", response_model=list[RecordOut])
def list_group_records(group_id: GroupId, user: CurrentUser, db: DbSession):
    return record_service.list_group_records(db, user, group_id)


@router.post("/{group_id}/records", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_group_record(group_id: GroupId, data: RecordIn, user: CurrentUser, db: DbSession):
    """Needs can_create_records (and can_assign_records when an assignee is set).
    The assignee must be a group member."""
    return record_service.create_in_group(db, user, group_id, data)

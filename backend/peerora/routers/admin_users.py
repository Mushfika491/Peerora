"""Admin: overview statistics and user management."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from peerora.core.dependencies import Client, DbSession, require_permission
from peerora.core.permissions import Permission
from peerora.models import User
from peerora.routers.admin_filters import AdminUser, Page, PageSize, UserFilterParams
from peerora.schemas import TutorOut
from peerora.schemas.admin import (
    AdminUserDetail,
    AdminUserOut,
    BanIn,
    BulkBanIn,
    BulkResult,
    BulkUnbanIn,
    OverviewOut,
    RoleChangeIn,
    TutorOwnerIn,
    UnbanIn,
)
from peerora.schemas.common import Page as PageOf
from peerora.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin: users"])

UserId = Annotated[int, Path(ge=1, le=2147483647)]
UserManager = Annotated[User, Depends(require_permission(Permission.USER_MANAGE))]
UserBanner = Annotated[User, Depends(require_permission(Permission.USER_BAN))]
RoleChanger = Annotated[User, Depends(require_permission(Permission.ROLE_CHANGE))]
SessionRevoker = Annotated[User, Depends(require_permission(Permission.SESSION_REVOKE_ANY))]
Moderator = Annotated[User, Depends(require_permission(Permission.CONTENT_MODERATE))]


@router.get("/overview", response_model=OverviewOut)
def overview(_: AdminUser, db: DbSession):
    return admin_service.overview(db)


@router.get("/users", response_model=PageOf[AdminUserOut])
def list_users(_: UserManager, db: DbSession, filters: UserFilterParams, page: Page = 1, page_size: PageSize = 20):
    users, total = admin_service.list_users(db, filters, page, page_size)
    return PageOf[AdminUserOut](
        items=[AdminUserOut.model_validate(u) for u in users], total=total, page=page, page_size=page_size
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def user_detail(user_id: UserId, _: UserManager, db: DbSession):
    return admin_service.user_detail(db, user_id)


@router.post("/users/bulk-ban", response_model=BulkResult)
def bulk_ban(data: BulkBanIn, admin: UserBanner, db: DbSession, client: Client):
    """Administrators and yourself are skipped (see the per-user results)."""
    return admin_service.bulk_ban(db, admin, data.user_ids, data.reason, client)


@router.post("/users/bulk-unban", response_model=BulkResult)
def bulk_unban(data: BulkUnbanIn, admin: UserBanner, db: DbSession, client: Client):
    return admin_service.bulk_unban(db, admin, data.user_ids, data.reason, client)


@router.post("/users/{user_id}/ban", response_model=AdminUserOut)
def ban_user(user_id: UserId, data: BanIn, admin: UserBanner, db: DbSession, client: Client):
    return admin_service.ban_user(db, admin, user_id, data.reason, client)


@router.post("/users/{user_id}/unban", response_model=AdminUserOut)
def unban_user(user_id: UserId, data: UnbanIn, admin: UserBanner, db: DbSession, client: Client):
    return admin_service.unban_user(db, admin, user_id, data.reason, client)


@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
def change_role(user_id: UserId, data: RoleChangeIn, admin: RoleChanger, db: DbSession, client: Client):
    return admin_service.change_role(db, admin, user_id, data.role, client)


@router.delete("/users/{user_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(user_id: UserId, session_id: str, admin: SessionRevoker, db: DbSession, client: Client):
    admin_service.revoke_user_session(db, admin, user_id, session_id, client)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users/{user_id}/sessions/revoke-all")
def revoke_all_sessions(user_id: UserId, admin: SessionRevoker, db: DbSession, client: Client) -> dict[str, int]:
    return {"revoked": admin_service.revoke_all_user_sessions(db, admin, user_id, client)}


@router.patch("/tutors/{tutor_id}/owner", response_model=TutorOut)
def set_tutor_owner(tutor_id: UserId, data: TutorOwnerIn, admin: Moderator, db: DbSession, client: Client):
    """Link a tutor profile (for example one created before accounts existed)
    to a tutor account, or unlink it with user_id null."""
    return admin_service.set_tutor_owner(db, admin, tutor_id, data.user_id, client)

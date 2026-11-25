"""Admin: content moderation of study records and study groups."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from peerora.core.dependencies import Client, DbSession, require_permission
from peerora.core.permissions import Permission
from peerora.models import User
from peerora.routers.admin_filters import GroupFilterParams, Page, PageSize, RecordFilterParams
from peerora.schemas.admin import AdminGroupDetail, AdminGroupOut, AdminRecordOut, BulkDeleteIn, BulkResult
from peerora.schemas.common import Page as PageOf
from peerora.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin: content"])

ItemId = Annotated[int, Path(ge=1, le=2147483647)]
Moderator = Annotated[User, Depends(require_permission(Permission.CONTENT_MODERATE))]


@router.get("/records", response_model=PageOf[AdminRecordOut])
def list_records(_: Moderator, db: DbSession, filters: RecordFilterParams, page: Page = 1, page_size: PageSize = 20):
    items, total = admin_service.list_records(db, filters, page, page_size)
    return PageOf[AdminRecordOut](items=items, total=total, page=page, page_size=page_size)


@router.delete("/records/{record_id}", response_model=BulkResult)
def delete_record(record_id: ItemId, admin: Moderator, db: DbSession, client: Client):
    return admin_service.delete_records(db, admin, [record_id], client)


@router.post("/records/bulk-delete", response_model=BulkResult)
def bulk_delete_records(data: BulkDeleteIn, admin: Moderator, db: DbSession, client: Client):
    return admin_service.delete_records(db, admin, data.ids, client)


@router.get("/groups", response_model=PageOf[AdminGroupOut])
def list_groups(_: Moderator, db: DbSession, filters: GroupFilterParams, page: Page = 1, page_size: PageSize = 20):
    items, total = admin_service.list_groups(db, filters, page, page_size)
    return PageOf[AdminGroupOut](items=items, total=total, page=page, page_size=page_size)


@router.get("/groups/{group_id}", response_model=AdminGroupDetail)
def group_detail(group_id: ItemId, _: Moderator, db: DbSession):
    return admin_service.group_detail(db, group_id)


@router.delete("/groups/{group_id}", response_model=BulkResult)
def delete_group(group_id: ItemId, admin: Moderator, db: DbSession, client: Client):
    return admin_service.delete_groups(db, admin, [group_id], client)


@router.post("/groups/bulk-delete", response_model=BulkResult)
def bulk_delete_groups(data: BulkDeleteIn, admin: Moderator, db: DbSession, client: Client):
    return admin_service.delete_groups(db, admin, data.ids, client)

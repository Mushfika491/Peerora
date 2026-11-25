"""Study records: the user's personal records, records assigned to them, and
single-record operations (personal or group). Rules: services/record_service.py."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Response, status

from peerora.core.dependencies import Client, CurrentUser, DbSession, require_permission
from peerora.core.permissions import Permission
from peerora.models import User
from peerora.schemas.record import RecordIn, RecordOut, RecordUpdate
from peerora.services import record_service

router = APIRouter(prefix="/api/records", tags=["study records"])

RecordId = Annotated[int, Path(ge=1, le=2147483647)]
RecordUser = Annotated[User, Depends(require_permission(Permission.RECORD_MANAGE_OWN))]


@router.get("", response_model=list[RecordOut])
def list_my_records(
    user: RecordUser, db: DbSession,
    scope: Annotated[Literal["personal", "assigned"], Query()] = "personal",
):
    """scope=personal: your private records. scope=assigned: group records assigned to you."""
    if scope == "assigned":
        return record_service.list_assigned(db, user)
    return record_service.list_personal(db, user)


@router.post("", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_personal_record(data: RecordIn, user: RecordUser, db: DbSession):
    return record_service.create_personal(db, user, data)


@router.get("/{record_id}", response_model=RecordOut)
def read_record(record_id: RecordId, user: CurrentUser, db: DbSession):
    record, membership = record_service.load_for_user(db, record_id, user)
    return record_service.to_record_out(record, user, membership)


@router.patch("/{record_id}", response_model=RecordOut)
def update_record(record_id: RecordId, data: RecordUpdate, user: CurrentUser, db: DbSession):
    return record_service.update_record(db, user, record_id, data)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: RecordId, user: CurrentUser, db: DbSession, client: Client):
    record_service.delete_record(db, user, record_id, client)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

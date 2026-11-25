"""One summary endpoint that feeds the Student and Tutor dashboards."""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from peerora import crud
from peerora.constants import RECORD_STATUSES
from peerora.core.dependencies import CurrentUser, DbSession
from peerora.schemas.group import GroupOut
from peerora.schemas.record import RecordOut
from peerora.services import group_service, record_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardSummary(BaseModel):
    account_type: str
    role: str
    groups: list[GroupOut]
    group_count: int
    record_counts: dict[str, int]  # visible records by status
    assigned_to_me: list[RecordOut]  # open group records assigned to the user
    personal_open: list[RecordOut]
    tutor_profile_id: int | None


@router.get("/summary", response_model=DashboardSummary)
def summary(user: CurrentUser, db: DbSession):
    visible = record_service.visible_records_query(user).subquery()
    counts = dict(
        db.execute(select(visible.c.status, func.count()).group_by(visible.c.status)).all()
    )
    groups = group_service.list_my_groups(db, user)
    tutor = crud.get_tutor_by_user(db, user.id)
    return DashboardSummary(
        account_type=user.account_type,
        role=user.role,
        groups=groups[:6],
        group_count=len(groups),
        record_counts={status: counts.get(status, 0) for status in RECORD_STATUSES},
        assigned_to_me=[r for r in record_service.list_assigned(db, user) if r.status != "done"][:6],
        personal_open=[r for r in record_service.list_personal(db, user) if r.status != "done"][:6],
        tutor_profile_id=tutor.id if tutor else None,
    )

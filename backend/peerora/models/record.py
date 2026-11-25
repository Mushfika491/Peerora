"""Study records: small tasks or notes.

group_id NULL  -> a personal record, visible only to its creator.
group_id set   -> a shared record, visible to the group's members.
assigned_to_id -> the group member responsible for it (must be a member;
                  checked in services/record_service.py).
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from peerora.constants import (
    RECORD_CONTENT_MAX_LENGTH,
    RECORD_STATUS_TODO,
    RECORD_STATUSES,
    RECORD_TITLE_MAX_LENGTH,
)
from peerora.core.timeutils import utcnow
from peerora.database import Base
from peerora.models.group import StudyGroup
from peerora.models.helpers import UtcDateTime, in_list
from peerora.models.user import User


class StudyRecord(Base):
    __tablename__ = "study_records"
    __table_args__ = (
        CheckConstraint("length(title) >= 1", name="ck_study_records_title_length"),
        CheckConstraint(in_list("status", RECORD_STATUSES), name="ck_study_records_status_allowed"),
        Index("ix_study_records_group_id", "group_id"),
        Index("ix_study_records_created_by_id", "created_by_id"),
        Index("ix_study_records_assigned_to_id", "assigned_to_id"),
        Index("ix_study_records_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", name="fk_study_records_created_by_id_users")
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("study_groups.id", ondelete="CASCADE", name="fk_study_records_group_id_study_groups")
    )
    title: Mapped[str] = mapped_column(String(RECORD_TITLE_MAX_LENGTH))
    content: Mapped[str | None] = mapped_column(String(RECORD_CONTENT_MAX_LENGTH))
    status: Mapped[str] = mapped_column(
        String(15), default=RECORD_STATUS_TODO, server_default=RECORD_STATUS_TODO
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL", name="fk_study_records_assigned_to_id_users")
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now(), onupdate=utcnow
    )

    creator: Mapped[User] = relationship(foreign_keys=[created_by_id], lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assigned_to_id], lazy="joined")
    group: Mapped[StudyGroup | None] = relationship(lazy="joined")

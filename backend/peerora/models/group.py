"""Study groups and their memberships.

Each membership stores three independent permissions for shared records:
can_create_records, can_update_records and can_assign_records. group_role is a
label derived from them (editor = all, viewer = none, member = a mix); the
owner has role "owner" and every permission. study_groups.owner_id is the
authoritative owner.
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from peerora.constants import (
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_NAME_MIN_LENGTH,
    GROUP_ROLES,
)
from peerora.core.timeutils import utcnow
from peerora.database import Base
from peerora.models.helpers import UtcDateTime, in_list
from peerora.models.user import User


class StudyGroup(Base):
    __tablename__ = "study_groups"
    __table_args__ = (
        CheckConstraint(
            f"length(name) >= {GROUP_NAME_MIN_LENGTH}", name="ck_study_groups_name_length"
        ),
        Index("ix_study_groups_owner_id", "owner_id"),
        Index("ix_study_groups_name", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(GROUP_NAME_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(String(GROUP_DESCRIPTION_MAX_LENGTH))
    subject: Mapped[str | None] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", name="fk_study_groups_owner_id_users")
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now(), onupdate=utcnow
    )

    owner: Mapped[User] = relationship(lazy="joined")


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_memberships_group_id_user_id"),
        CheckConstraint(in_list("group_role", GROUP_ROLES), name="ck_group_memberships_role_allowed"),
        Index("ix_group_memberships_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("study_groups.id", ondelete="CASCADE", name="fk_group_memberships_group_id_study_groups")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", name="fk_group_memberships_user_id_users")
    )
    group_role: Mapped[str] = mapped_column(String(10))
    can_create_records: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    can_update_records: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    can_assign_records: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    added_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL", name="fk_group_memberships_added_by_id_users")
    )
    joined_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now()
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id], lazy="joined")

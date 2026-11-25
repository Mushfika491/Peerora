"""User accounts.

account_type (student/tutor) decides the application experience.
role (user/admin) decides what the backend authorizes. They are independent.
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from peerora.constants import (
    ACCOUNT_TYPES,
    BAN_REASON_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    ROLE_USER,
    ROLES,
    USER_FULL_NAME_MAX_LENGTH,
)
from peerora.core.timeutils import utcnow
from peerora.database import Base
from peerora.models.helpers import UtcDateTime, in_list


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(in_list("account_type", ACCOUNT_TYPES), name="ck_users_account_type_allowed"),
        CheckConstraint(in_list("role", ROLES), name="ck_users_role_allowed"),
        # A banned account must always say why it was banned.
        CheckConstraint("NOT is_banned OR ban_reason IS NOT NULL", name="ck_users_ban_has_reason"),
        Index("ix_users_role", "role"),
        Index("ix_users_is_banned", "is_banned"),
        Index("ix_users_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stored in lowercase so uniqueness is case-insensitive.
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH))
    full_name: Mapped[str] = mapped_column(String(USER_FULL_NAME_MAX_LENGTH))
    # Argon2id hash of the peppered password. Never returned by the API.
    password_hash: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(10))
    role: Mapped[str] = mapped_column(String(10), default=ROLE_USER, server_default=ROLE_USER)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    ban_reason: Mapped[str | None] = mapped_column(String(BAN_REASON_MAX_LENGTH))
    banned_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    banned_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL", name="fk_users_banned_by_id_users")
    )

    last_login_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now(), onupdate=utcnow
    )

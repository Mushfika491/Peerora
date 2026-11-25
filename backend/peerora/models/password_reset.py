"""Password-reset tokens.

The emailed token is a random 256-bit value; only its SHA-256 hash is stored,
so a database leak does not reveal usable reset links. A token is valid until
expires_at and can be used once (used_at). Requesting a new link marks older
unused links as used, so only the newest link works.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from peerora.core.timeutils import utcnow
from peerora.database import Base
from peerora.models.helpers import UtcDateTime


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
        Index("ix_password_reset_tokens_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", name="fk_password_reset_tokens_user_id_users")
    )
    token_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    used_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    requested_ip: Mapped[str | None] = mapped_column(String(45))

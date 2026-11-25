"""Login sessions and their rotating refresh tokens.

A UserSession is one signed-in device. Its id travels inside every access
token (the "sid" claim), so revoking the session ends access immediately.
Each refresh replaces the session's RefreshToken with a new one; the old row
is kept with used_at set, so presenting it again is detected as token reuse.
Only SHA-256 hashes of refresh tokens are stored.
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from peerora.core.timeutils import utcnow
from peerora.database import Base
from peerora.models.helpers import UtcDateTime


def _new_session_id() -> str:
    return str(uuid.uuid4())


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (Index("ix_user_sessions_user_id_revoked_at", "user_id", "revoked_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_session_id)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", name="fk_user_sessions_user_id_users")
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now()
    )
    last_used_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    # logout, user_revoked, admin_revoked, password_changed, banned, token_reuse
    revoked_reason: Mapped[str | None] = mapped_column(String(30))


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("user_sessions.id", ondelete="CASCADE", name="fk_refresh_tokens_session_id_user_sessions"),
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    # Set when this token is exchanged for a new one. A used token is never valid again.
    used_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=utcnow, server_default=func.now()
    )

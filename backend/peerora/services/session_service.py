"""Login sessions and refresh-token rotation.

start_session  - creates a session and its first refresh token.
rotate         - exchanges a refresh token for a new one (the old one becomes
                 "used"). Presenting a used token again means it was probably
                 stolen, so the whole session is revoked - unless it happens
                 within a few seconds of the rotation (REFRESH_REUSE_GRACE_SECONDS),
                 which is what two tabs refreshing at once or a retried request
                 look like. Then a fresh token is issued instead.
revoke_*       - end one or all sessions of a user.
"""

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from peerora.config import get_refresh_token_days
from peerora.constants import REFRESH_REUSE_GRACE_SECONDS
from peerora.core.dependencies import account_suspended
from peerora.core.request_info import ClientInfo
from peerora.core.security import hash_token, new_refresh_token
from peerora.core.timeutils import as_utc, utcnow
from peerora.models import RefreshToken, User, UserSession
from peerora.services.audit_service import AuditAction, log_event

INVALID_REFRESH_MESSAGE = "Your session has expired. Please log in again."


def _issue_refresh_token(db: Session, session: UserSession) -> str:
    raw = new_refresh_token()
    expires_at = utcnow() + timedelta(days=get_refresh_token_days())
    session.expires_at = expires_at  # sliding expiry: each refresh extends the session
    db.add(RefreshToken(session_id=session.id, token_hash=hash_token(raw), expires_at=expires_at))
    return raw


def start_session(db: Session, user: User, client: ClientInfo) -> tuple[UserSession, str]:
    session = UserSession(
        user_id=user.id,
        ip_address=client.ip_address,
        user_agent=client.user_agent,
        expires_at=utcnow() + timedelta(days=get_refresh_token_days()),
    )
    db.add(session)
    db.flush()  # assigns the session id
    return session, _issue_refresh_token(db, session)


def revoke_session(session: UserSession, reason: str) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        session.revoked_reason = reason


def revoke_all_sessions(
    db: Session, user_id: int, reason: str, except_session_id: str | None = None
) -> int:
    statement = (
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=utcnow(), revoked_reason=reason)
    )
    if except_session_id is not None:
        statement = statement.where(UserSession.id != except_session_id)
    return db.execute(statement).rowcount or 0


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_REFRESH_MESSAGE)


def rotate(db: Session, raw_token: str, client: ClientInfo) -> tuple[User, UserSession, str]:
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if token is None:
        raise _unauthorized()
    session = db.get(UserSession, token.session_id)
    if session is None:
        raise _unauthorized()

    now = utcnow()
    session_alive = session.revoked_at is None and as_utc(session.expires_at) > now
    recently_rotated = (
        token.used_at is not None
        and now - as_utc(token.used_at) <= timedelta(seconds=REFRESH_REUSE_GRACE_SECONDS)
    )
    if token.used_at is not None and not (recently_rotated and session_alive):
        # Reuse of an old token: end the session so neither copy works any more.
        revoke_session(session, "token_reuse")
        log_event(
            db, AuditAction.TOKEN_REUSE_DETECTED, client,
            actor_id=session.user_id, target_user_id=session.user_id,
            target_type="session", target_id=session.id,
        )
        db.commit()
        raise _unauthorized()

    if not session_alive or as_utc(token.expires_at) <= now:
        raise _unauthorized()

    user = db.get(User, session.user_id)
    if user is None:
        raise _unauthorized()
    if user.is_banned:
        revoke_session(session, "banned")
        db.commit()
        raise account_suspended()

    if token.used_at is None:
        token.used_at = now  # a token inside the grace window keeps its original time
    session.last_used_at = now
    session.ip_address = client.ip_address
    session.user_agent = client.user_agent
    new_raw = _issue_refresh_token(db, session)
    db.commit()
    return user, session, new_raw


def find_session_by_refresh_token(db: Session, raw_token: str) -> UserSession | None:
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    return None if token is None else db.get(UserSession, token.session_id)


def list_active_sessions(db: Session, user_id: int) -> list[UserSession]:
    sessions = db.scalars(
        select(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.last_used_at.desc())
    ).all()
    now = utcnow()
    return [item for item in sessions if as_utc(item.expires_at) > now]

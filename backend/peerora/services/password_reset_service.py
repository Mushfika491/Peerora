"""Forgotten-password flow.

request_reset  - always answers the same way, whether or not the email has an
                 account (no account enumeration). For a real, non-banned
                 account it stores the SHA-256 hash of a new random token and
                 queues an email with the link. Rate limited per IP (429) and
                 per account (silently: no more emails, same reply).
complete_reset - checks the token (exists, unused, not expired), sets the new
                 password, marks the token used, invalidates the user's other
                 reset links and signs out every session.

The raw token appears only in the emailed link, after "#", so browsers never
send it to any server in a URL or Referer header, and it is never logged.
"""

import logging
from datetime import timedelta

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from peerora.config import get_public_app_url
from peerora.constants import (
    MAX_PASSWORD_RESET_EMAILS_PER_ACCOUNT,
    MAX_PASSWORD_RESET_REQUESTS_PER_IP,
    PASSWORD_RESET_TOKEN_MINUTES,
    PASSWORD_RESET_WINDOW_MINUTES,
)
from peerora.core.request_info import ClientInfo
from peerora.core.security import hash_password, hash_token, new_refresh_token
from peerora.core.timeutils import as_utc, utcnow
from peerora.models import AuditLog, PasswordResetToken, User
from peerora.services import email_service, session_service
from peerora.services.audit_service import AuditAction, log_event

logger = logging.getLogger("peerora.password_reset")

GENERIC_REQUEST_REPLY = (
    "If an account exists for that email address, a password-reset link has been sent. "
    f"The link expires in {PASSWORD_RESET_TOKEN_MINUTES} minutes."
)
INVALID_TOKEN_MESSAGE = "This password-reset link is invalid or has expired. Please request a new one."
RATE_LIMIT_MESSAGE = "Too many password-reset requests from your network. Please try again later."
UNAVAILABLE_MESSAGE = (
    "Password reset by email is not available on this server yet. Please contact an administrator."
)


def _requests_from_ip(db: Session, ip_address: str | None) -> int:
    if ip_address is None:
        return 0
    since = utcnow() - timedelta(minutes=PASSWORD_RESET_WINDOW_MINUTES)
    return db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.action == str(AuditAction.PASSWORD_RESET_REQUESTED),
            AuditLog.ip_address == ip_address,
            AuditLog.created_at >= since,
        )
    ) or 0


def _emails_for_account(db: Session, user_id: int) -> int:
    since = utcnow() - timedelta(minutes=PASSWORD_RESET_WINDOW_MINUTES)
    return db.scalar(
        select(func.count(PasswordResetToken.id)).where(
            PasswordResetToken.user_id == user_id, PasswordResetToken.created_at >= since
        )
    ) or 0


def retire_outstanding_tokens(db: Session, user_id: int) -> int:
    """Mark every unused reset link of this one account as used, so none of them
    works any more. Other accounts' links are not touched. Returns how many."""
    result = db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at.is_(None))
        .values(used_at=utcnow())
    )
    return result.rowcount or 0


def reset_link(raw_token: str) -> str:
    return f"{get_public_app_url()}/reset-password#token={raw_token}"


def _email_body(name: str, link: str) -> str:
    return (
        f"Hello {name},\n\n"
        "Someone (hopefully you) asked to reset the password of your Peerora account.\n"
        f"Open this link within {PASSWORD_RESET_TOKEN_MINUTES} minutes to choose a new password:\n\n"
        f"{link}\n\n"
        "The link works only once. If you did not ask for this, you can ignore this email: "
        "your password stays the same.\n\n"
        "- Peerora\n"
    )


def deliver_reset_email(to: str, name: str, raw_token: str) -> None:
    """Runs after the response is sent (BackgroundTasks), so the reply takes the
    same time whether or not an email goes out. Never logs the token or link."""
    try:
        email_service.send_email(to, "Reset your Peerora password", _email_body(name, reset_link(raw_token)))
    except (email_service.EmailDeliveryError, email_service.EmailNotConfiguredError) as error:
        logger.warning("Password-reset email could not be delivered (%s).", error)


def request_reset(db: Session, email: str, client: ClientInfo, background: BackgroundTasks) -> str:
    if not email_service.is_email_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE_MESSAGE)
    # Per-IP limit (does not depend on the email, so it reveals nothing about accounts).
    if _requests_from_ip(db, client.ip_address) >= MAX_PASSWORD_RESET_REQUESTS_PER_IP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RATE_LIMIT_MESSAGE,
            headers={"Retry-After": str(PASSWORD_RESET_WINDOW_MINUTES * 60)},
        )

    user = db.scalar(select(User).where(User.email == email))
    outcome = "unknown_email"
    if user is not None and user.is_banned:
        outcome = "account_suspended"
    elif user is not None and _emails_for_account(db, user.id) >= MAX_PASSWORD_RESET_EMAILS_PER_ACCOUNT:
        outcome = "account_rate_limited"  # stops someone flooding a person's inbox
    elif user is not None:
        now = utcnow()
        # Only the newest link works: retire any older unused ones.
        retire_outstanding_tokens(db, user.id)
        raw_token = new_refresh_token()  # 256 random bits, URL-safe
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=now + timedelta(minutes=PASSWORD_RESET_TOKEN_MINUTES),
            requested_ip=client.ip_address,
        ))
        background.add_task(deliver_reset_email, user.email, user.full_name, raw_token)
        outcome = "email_queued"

    # Every request is audited (also used for the per-IP limit). The token is never logged.
    log_event(db, AuditAction.PASSWORD_RESET_REQUESTED, client,
              target_user_id=user.id if user else None,
              details={"email": email, "outcome": outcome})
    db.commit()
    return GENERIC_REQUEST_REPLY


def complete_reset(db: Session, raw_token: str, new_password: str, client: ClientInfo) -> None:
    record = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw_token)))
    now = utcnow()
    if record is None or record.used_at is not None or as_utc(record.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_TOKEN_MESSAGE)
    user = db.get(User, record.user_id)
    if user is None or user.is_banned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_TOKEN_MESSAGE)
    if new_password.strip().lower() == user.email:
        raise HTTPException(status_code=422, detail="New password must not be the same as your email address.")

    user.password_hash = hash_password(new_password)
    record.used_at = now
    # Any other outstanding links for this account stop working too.
    retire_outstanding_tokens(db, user.id)
    revoked = session_service.revoke_all_sessions(db, user.id, "password_reset")
    log_event(db, AuditAction.PASSWORD_RESET_COMPLETED, client, actor_id=user.id, target_user_id=user.id,
              details={"sessions_revoked": revoked})
    db.commit()

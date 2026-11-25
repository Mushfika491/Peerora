"""Signup, login (with brute-force protection), logout and password changes."""

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from peerora.constants import (
    LOGIN_WINDOW_MINUTES,
    MAX_FAILED_LOGINS_PER_ACCOUNT,
    MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP,
    MAX_FAILED_LOGINS_PER_IP,
    MAX_SIGNUPS_PER_IP,
    ROLE_USER,
    SIGNUP_WINDOW_MINUTES,
)
from peerora.core.dependencies import account_suspended
from peerora.core.request_info import ClientInfo
from peerora.core.security import (
    burn_password_check_time,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from peerora.core.timeutils import utcnow
from peerora.models import AuditLog, LoginAttempt, Tutor, User, UserSession
from peerora.schemas.auth import SignupIn
from peerora.schemas.user import UserOut
from peerora.services import session_service
from peerora.services.audit_service import AuditAction, log_event

INVALID_CREDENTIALS_MESSAGE = "Incorrect email or password."
THROTTLED_MESSAGE = "Too many failed login attempts. Please wait a few minutes and try again."
DUPLICATE_EMAIL_MESSAGE = "An account with this email address already exists."
SIGNUP_THROTTLED_MESSAGE = "Too many accounts were created from your network recently. Please try again later."


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def to_user_out(db: Session, user: User) -> UserOut:
    has_profile = db.scalar(select(Tutor.id).where(Tutor.user_id == user.id).limit(1)) is not None
    return UserOut.model_validate(user).model_copy(update={"has_tutor_profile": has_profile})


def _recent_signups(db: Session, ip_address: str | None) -> int:
    """Successful signups from this IP address in the signup window (from the audit log)."""
    if ip_address is None:
        return 0
    since = utcnow() - timedelta(minutes=SIGNUP_WINDOW_MINUTES)
    return db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.action == str(AuditAction.SIGNUP),
            AuditLog.ip_address == ip_address,
            AuditLog.created_at >= since,
        )
    ) or 0


def signup(db: Session, data: SignupIn, client: ClientInfo) -> tuple[User, UserSession, str]:
    # Rate limit: stops one address from creating accounts in bulk.
    if _recent_signups(db, client.ip_address) >= MAX_SIGNUPS_PER_IP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=SIGNUP_THROTTLED_MESSAGE,
            headers={"Retry-After": str(SIGNUP_WINDOW_MINUTES * 60)},
        )
    if get_user_by_email(db, data.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_EMAIL_MESSAGE)
    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        account_type=data.account_type,
        role=ROLE_USER,  # public signup can never create an administrator
        last_login_at=utcnow(),
    )
    db.add(user)
    db.flush()
    log_event(db, AuditAction.SIGNUP, client, actor_id=user.id, target_user_id=user.id,
              details={"account_type": user.account_type})
    session, refresh_token = session_service.start_session(db, user, client)
    db.commit()
    return user, session, refresh_token


def _recent_failures(db: Session, *, email: str | None = None, ip_address: str | None = None) -> int:
    """Real wrong-password attempts in the login window matching the given email
    and/or IP address. Attempts refused because of throttling are NOT counted:
    they never reached a password check, so an attacker who keeps hammering one
    account from one address cannot push the account into a global lockout."""
    since = utcnow() - timedelta(minutes=LOGIN_WINDOW_MINUTES)
    statement = select(func.count(LoginAttempt.id)).where(
        LoginAttempt.failure_reason == "bad_credentials", LoginAttempt.created_at >= since
    )
    if email is not None:
        statement = statement.where(LoginAttempt.email == email)
    if ip_address is not None:
        statement = statement.where(LoginAttempt.ip_address == ip_address)
    return db.scalar(statement) or 0


def is_login_throttled(db: Session, email: str, ip_address: str | None) -> bool:
    """Three limits (see constants.py):
    - per account AND address: blocks guessing one account from one network,
      without locking the real owner out from their own network;
    - per address: blocks one network guessing many accounts;
    - per account (much higher): blocks guessing spread over many networks."""
    if ip_address is not None:
        if _recent_failures(db, email=email, ip_address=ip_address) >= MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP:
            return True
        if _recent_failures(db, ip_address=ip_address) >= MAX_FAILED_LOGINS_PER_IP:
            return True
    return _recent_failures(db, email=email) >= MAX_FAILED_LOGINS_PER_ACCOUNT


def _record_attempt(
    db: Session, email: str, client: ClientInfo, user: User | None, success: bool, reason: str | None
) -> None:
    db.add(LoginAttempt(
        email=email,
        user_id=user.id if user else None,
        ip_address=client.ip_address,
        user_agent=client.user_agent,
        success=success,
        failure_reason=reason,
    ))
    if success:
        log_event(db, AuditAction.LOGIN_SUCCESS, client, actor_id=user.id, target_user_id=user.id)
    else:
        log_event(db, AuditAction.LOGIN_FAILED, client,
                  target_user_id=user.id if user else None,
                  details={"email": email, "reason": reason})


def login(db: Session, email: str, password: str, client: ClientInfo) -> tuple[User, UserSession, str]:
    # 1. Brute-force protection (stored in the database, so it also works on
    #    serverless hosting where each request may run on a different instance).
    if is_login_throttled(db, email, client.ip_address):
        _record_attempt(db, email, client, get_user_by_email(db, email), False, "throttled")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=THROTTLED_MESSAGE,
            headers={"Retry-After": str(LOGIN_WINDOW_MINUTES * 60)},
        )

    # 2. Check the credentials. The same message is used for an unknown email
    #    and a wrong password, so attackers cannot discover which emails exist.
    user = get_user_by_email(db, email)
    if user is None:
        burn_password_check_time(password)
    if user is None or not verify_password(password, user.password_hash):
        _record_attempt(db, email, client, user, False, "bad_credentials")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS_MESSAGE)

    # 3. Banned accounts cannot sign in.
    if user.is_banned:
        _record_attempt(db, email, client, user, False, "banned")
        db.commit()
        raise account_suspended()

    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.last_login_at = utcnow()
    _record_attempt(db, email, client, user, True, None)
    session, refresh_token = session_service.start_session(db, user, client)
    db.commit()
    return user, session, refresh_token


def logout(db: Session, raw_refresh_token: str | None, client: ClientInfo) -> None:
    if not raw_refresh_token:
        return
    session = session_service.find_session_by_refresh_token(db, raw_refresh_token)
    if session is None or session.revoked_at is not None:
        return
    session_service.revoke_session(session, "logout")
    log_event(db, AuditAction.LOGOUT, client, actor_id=session.user_id,
              target_user_id=session.user_id, target_type="session", target_id=session.id)
    db.commit()


def change_password(
    db: Session, user: User, current_password: str, new_password: str,
    current_session_id: str | None, client: ClientInfo,
) -> int:
    """Returns how many other sessions were signed out."""
    if not verify_password(current_password, user.password_hash):
        # 400, not 401: the user is still logged in, the form input is just wrong.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    if verify_password(new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="The new password must be different from the current password.")
    user.password_hash = hash_password(new_password)
    revoked = session_service.revoke_all_sessions(
        db, user.id, "password_changed", except_session_id=current_session_id
    )
    log_event(db, AuditAction.PASSWORD_CHANGED, client, actor_id=user.id, target_user_id=user.id,
              details={"other_sessions_revoked": revoked})
    db.commit()
    return revoked

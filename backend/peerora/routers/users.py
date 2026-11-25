"""The signed-in user's own account: profile, password and sessions."""

from fastapi import APIRouter, HTTPException, Request, Response, status

from peerora.core.dependencies import Client, CurrentUser, DbSession
from peerora.core.security import verify_password
from peerora.models import UserSession
from peerora.schemas.user import PasswordChangeIn, ProfileUpdateIn, SessionOut, UserOut
from peerora.services import auth_service, password_reset_service, session_service
from peerora.services.audit_service import AuditAction, log_event

router = APIRouter(prefix="/api/users/me", tags=["account"])


@router.get("", response_model=UserOut)
def read_me(user: CurrentUser, db: DbSession):
    return auth_service.to_user_out(db, user)


@router.patch("", response_model=UserOut)
def update_me(data: ProfileUpdateIn, user: CurrentUser, db: DbSession, client: Client):
    """Update your name and/or email. The role and account type cannot be changed here."""
    changed: list[str] = []
    if data.full_name is not None and data.full_name != user.full_name:
        user.full_name = data.full_name
        changed.append("full_name")
    if data.email is not None and data.email != user.email:
        if not data.current_password or not verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Enter your current password to change your email address.")
        if auth_service.get_user_by_email(db, data.email) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=auth_service.DUPLICATE_EMAIL_MESSAGE)
        user.email = data.email
        changed.append("email")
        # A reset link already sent to the old address must not work any more.
        password_reset_service.retire_outstanding_tokens(db, user.id)
    if changed:
        log_event(db, AuditAction.PROFILE_UPDATED, client, actor_id=user.id, target_user_id=user.id,
                  details={"fields": changed})
        db.commit()
    return auth_service.to_user_out(db, user)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: PasswordChangeIn, request: Request, user: CurrentUser, db: DbSession, client: Client):
    """Requires the current password. Signs out every other device."""
    auth_service.change_password(
        db, user, data.current_password, data.new_password,
        getattr(request.state, "session_id", None), client,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(request: Request, user: CurrentUser, db: DbSession):
    current = getattr(request.state, "session_id", None)
    return [
        SessionOut(
            id=s.id, ip_address=s.ip_address, user_agent=s.user_agent, created_at=s.created_at,
            last_used_at=s.last_used_at, expires_at=s.expires_at, is_current=s.id == current,
        )
        for s in session_service.list_active_sessions(db, user.id)
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(session_id: str, user: CurrentUser, db: DbSession, client: Client):
    session = db.get(UserSession, session_id)
    # Another user's session id gives the same 404 as a missing one (no IDOR).
    if session is None or session.user_id != user.id or session.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    session_service.revoke_session(session, "user_revoked")
    log_event(db, AuditAction.SESSION_REVOKED, client, actor_id=user.id, target_user_id=user.id,
              target_type="session", target_id=session_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

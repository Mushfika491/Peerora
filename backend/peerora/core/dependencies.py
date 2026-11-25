"""FastAPI dependencies that authenticate and authorize every protected request.

get_current_user  - 401 unless a valid access token for a live session is sent;
                    403 if the account is banned.
require_permission - 403 unless the user's security role holds the permission.
require_account_type - 403 unless the user has the given account type
                    (an application capability, e.g. owning a tutor profile).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from peerora.core.permissions import Permission, has_permission
from peerora.core.request_info import ClientInfo, get_client_info
from peerora.core.security import InvalidTokenError, decode_access_token
from peerora.core.timeutils import as_utc, utcnow
from peerora.database import get_db
from peerora.models import User, UserSession

DbSession = Annotated[Session, Depends(get_db)]
Client = Annotated[ClientInfo, Depends(get_client_info)]

_bearer = HTTPBearer(auto_error=False, description="Access token from /api/auth/login")

SUSPENDED_MESSAGE = "Your account has been suspended. Contact an administrator."
# Lets the frontend tell "account suspended" apart from ordinary 403 errors
# (e.g. "you cannot edit this record") and sign the user out only for the former.
ERROR_CODE_HEADER = "X-Error-Code"
ACCOUNT_SUSPENDED_CODE = "account_suspended"


def account_suspended() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=SUSPENDED_MESSAGE,
        headers={ERROR_CODE_HEADER: ACCOUNT_SUSPENDED_CODE},
    )


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise _unauthorized("Not authenticated. Please log in.")
    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise _unauthorized("Your session token is invalid or has expired.") from None

    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise _unauthorized("Your session token is invalid or has expired.")
    if user.is_banned:
        raise account_suspended()

    session = db.get(UserSession, payload["sid"])
    if (
        session is None
        or session.user_id != user.id
        or session.revoked_at is not None
        or as_utc(session.expires_at) <= utcnow()
    ):
        raise _unauthorized("This session has ended. Please log in again.")

    # The role is always read from the database. A token issued before a role
    # change is refused, so the client refreshes and receives the new role.
    if payload["role"] != user.role:
        raise _unauthorized("Your permissions changed. Please refresh your session.")

    request.state.session_id = session.id
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_optional_user(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User | None:
    """For public endpoints that show extra data to the owner or an admin."""
    if credentials is None:
        return None
    try:
        return get_current_user(request, db, credentials)
    except HTTPException:
        return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_permission(permission: Permission) -> Callable[[User], User]:
    def checker(user: CurrentUser) -> User:
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return checker


def require_account_type(account_type: str) -> Callable[[User], User]:
    def checker(user: CurrentUser) -> User:
        if user.account_type != account_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only {account_type} accounts can perform this action.",
            )
        return user

    return checker

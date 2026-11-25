"""Signup, login, token refresh and logout.

The access token is returned in the JSON body (the frontend keeps it in memory).
The refresh token is only ever sent as an HttpOnly cookie that JavaScript
cannot read, scoped to /api/auth and SameSite=Strict.
"""

from fastapi import APIRouter, BackgroundTasks, Cookie, Header, HTTPException, Response, status
from fastapi.responses import JSONResponse

from peerora.config import (
    CSRF_HEADER_NAME,
    CSRF_HEADER_VALUE,
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    cookie_secure,
    get_access_token_minutes,
    get_refresh_token_days,
)
from peerora.core.dependencies import Client, DbSession
from peerora.core.security import create_access_token
from peerora.models import User, UserSession
from peerora.constants import PASSWORD_RESET_TOKEN_MINUTES
from peerora.schemas.auth import (
    LoginIn,
    MessageOut,
    PasswordResetAvailabilityOut,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
    SignupIn,
    TokenOut,
)
from peerora.services import auth_service, email_service, password_reset_service, session_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=get_refresh_token_days() * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=cookie_secure(),
        samesite="strict",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH,
        httponly=True, secure=cookie_secure(), samesite="strict",
    )


def _token_response(db, response: Response, user: User, session: UserSession, refresh_token: str) -> TokenOut:
    _set_refresh_cookie(response, refresh_token)
    return TokenOut(
        access_token=create_access_token(user.id, user.role, session.id),
        expires_in=get_access_token_minutes() * 60,
        user=auth_service.to_user_out(db, user),
    )


def _require_csrf_header(value: str | None) -> None:
    """Cookie-authenticated endpoints also need a custom header. Other sites
    cannot add custom headers to cross-site requests, which blocks CSRF."""
    if value != CSRF_HEADER_VALUE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing or invalid request header.")


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(data: SignupIn, response: Response, db: DbSession, client: Client):
    """Create a Student or Tutor account (always security role "user") and sign in."""
    user, session, refresh_token = auth_service.signup(db, data, client)
    return _token_response(db, response, user, session, refresh_token)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, response: Response, db: DbSession, client: Client):
    user, session, refresh_token = auth_service.login(db, data.email, data.password, client)
    return _token_response(db, response, user, session, refresh_token)


@router.post("/refresh", response_model=TokenOut, responses={401: {"description": "No valid session"}})
def refresh(
    response: Response,
    db: DbSession,
    client: Client,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    csrf: str | None = Header(default=None, alias=CSRF_HEADER_NAME),
):
    """Exchange the refresh cookie for a new access token and a new refresh cookie."""
    _require_csrf_header(csrf)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")
    try:
        user, session, new_token = session_service.rotate(db, refresh_token, client)
    except HTTPException as error:
        # A dead refresh token is also removed from the browser.
        failed = JSONResponse(status_code=error.status_code, content={"detail": error.detail})
        _clear_refresh_cookie(failed)
        return failed
    return _token_response(db, response, user, session, new_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    db: DbSession,
    client: Client,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    csrf: str | None = Header(default=None, alias=CSRF_HEADER_NAME),
):
    """Revoke this device's session and delete the refresh cookie."""
    _require_csrf_header(csrf)
    auth_service.logout(db, refresh_token, client)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_refresh_cookie(response)
    return response


# ---- Forgotten password ----

@router.get("/password-reset/availability", response_model=PasswordResetAvailabilityOut)
def password_reset_availability():
    """Whether reset-by-email works on this server (an email backend is configured).
    The frontend uses this to say so honestly instead of pretending to send email."""
    return PasswordResetAvailabilityOut(
        available=email_service.is_email_configured(), token_minutes=PASSWORD_RESET_TOKEN_MINUTES
    )


@router.post(
    "/password-reset/request",
    response_model=MessageOut,
    status_code=status.HTTP_202_ACCEPTED,
    responses={429: {"description": "Too many requests"}, 503: {"description": "Email not configured"}},
)
def request_password_reset(data: PasswordResetRequestIn, background: BackgroundTasks, db: DbSession, client: Client):
    """Always the same reply, whether or not the email has an account."""
    return MessageOut(detail=password_reset_service.request_reset(db, data.email, client, background))


@router.post("/password-reset/confirm", response_model=MessageOut)
def confirm_password_reset(data: PasswordResetConfirmIn, db: DbSession, client: Client):
    """Set a new password with a valid, unused, unexpired reset token.
    Signs out every existing session of the account."""
    password_reset_service.complete_reset(db, data.token, data.new_password, client)
    return MessageOut(detail="Your password has been reset. Please log in with your new password.")

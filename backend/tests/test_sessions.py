"""Refresh-token rotation, reuse detection, revocation and the sessions list."""

from datetime import timedelta

from sqlalchemy import select, update

from peerora.config import REFRESH_COOKIE_NAME
from peerora.constants import REFRESH_REUSE_GRACE_SECONDS
from peerora.core.timeutils import utcnow
from peerora.models import AuditLog, RefreshToken, User, UserSession
from tests.base import CSRF, ApiTestCase


class RefreshTokenTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = self.make_user(email="sam@example.com")
        self.assertEqual(self.login("sam@example.com").status_code, 200)

    def cookie(self) -> str:
        return self.client.cookies.get(REFRESH_COOKIE_NAME)

    def refresh_with(self, raw_token: str):
        client = self.new_client()
        client.cookies.set(REFRESH_COOKIE_NAME, raw_token, path="/api/auth")
        return client.post("/api/auth/refresh", headers=CSRF)

    def test_refresh_rotates_the_token(self) -> None:
        first = self.cookie()
        response = self.client.post("/api/auth/refresh", headers=CSRF)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        second = self.cookie()
        self.assertNotEqual(first, second)
        with self.session_factory() as db:
            tokens = db.scalars(select(RefreshToken)).all()
            self.assertEqual(len(tokens), 2)
            self.assertEqual(sum(t.used_at is not None for t in tokens), 1)
            # Only hashes are stored, never the raw token.
            self.assertNotIn(first, [t.token_hash for t in tokens])

    def age_used_tokens(self, seconds: int = REFRESH_REUSE_GRACE_SECONDS + 5) -> None:
        """Pretend every rotated token was rotated `seconds` ago (beyond the grace window)."""
        with self.session_factory() as db:
            db.execute(update(RefreshToken).where(RefreshToken.used_at.is_not(None))
                       .values(used_at=utcnow() - timedelta(seconds=seconds)))
            db.commit()

    def test_new_token_works_and_old_token_is_rejected(self) -> None:
        old = self.cookie()
        self.client.post("/api/auth/refresh", headers=CSRF)
        new = self.cookie()
        self.assertEqual(self.refresh_with(new).status_code, 200)
        self.age_used_tokens()
        self.assertEqual(self.refresh_with(old).status_code, 401)

    def test_concurrent_refresh_within_grace_window_keeps_the_session(self) -> None:
        """Two tabs refreshing at the same moment present the same token twice."""
        old = self.cookie()
        first = self.refresh_with(old)
        second = self.refresh_with(old)  # same token again, a moment later
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        with self.session_factory() as db:
            session = db.scalar(select(UserSession))
            self.assertIsNone(session.revoked_at)
            self.assertNotIn("token_reuse_detected", db.scalars(select(AuditLog.action)).all())
        # Both newly issued tokens belong to the same, still active session.
        self.assertEqual(self.refresh_with(second.cookies[REFRESH_COOKIE_NAME]).status_code, 200)

    def test_grace_window_never_revives_a_logged_out_session(self) -> None:
        old = self.cookie()
        self.client.post("/api/auth/refresh", headers=CSRF)
        self.client.post("/api/auth/logout", headers=CSRF)
        self.assertEqual(self.refresh_with(old).status_code, 401)

    def test_reusing_a_rotated_token_revokes_the_whole_session(self) -> None:
        old = self.cookie()
        self.client.post("/api/auth/refresh", headers=CSRF)
        current = self.cookie()
        self.age_used_tokens()
        self.assertEqual(self.refresh_with(old).status_code, 401)  # reuse detected
        # Even the legitimate newest token is now dead.
        self.assertEqual(self.refresh_with(current).status_code, 401)
        with self.session_factory() as db:
            session = db.scalar(select(UserSession))
            self.assertEqual(session.revoked_reason, "token_reuse")
            self.assertIn("token_reuse_detected", db.scalars(select(AuditLog.action)).all())

    def test_unknown_or_missing_refresh_token(self) -> None:
        self.assertEqual(self.refresh_with("made-up-token").status_code, 401)
        self.assertEqual(self.new_client().post("/api/auth/refresh", headers=CSRF).status_code, 401)

    def test_failed_refresh_clears_the_cookie(self) -> None:
        response = self.refresh_with("made-up-token")
        self.assertIn(f'{REFRESH_COOKIE_NAME}=""', response.headers["set-cookie"])

    def test_banned_user_cannot_refresh(self) -> None:
        with self.session_factory() as db:
            user = db.get(User, self.user.id)
            user.is_banned = True
            user.ban_reason = "Spam"
            db.commit()
        self.assertEqual(self.client.post("/api/auth/refresh", headers=CSRF).status_code, 403)


class SessionListTests(ApiTestCase):
    def test_list_and_revoke_own_sessions(self) -> None:
        user = self.make_user()
        current = self.auth(user)
        other = self.auth(user)
        sessions = self.client.get("/api/users/me/sessions", headers=current).json()
        self.assertEqual(len(sessions), 2)
        self.assertEqual(sum(s["is_current"] for s in sessions), 1)
        other_id = next(s["id"] for s in sessions if not s["is_current"])

        self.assertEqual(self.client.delete(f"/api/users/me/sessions/{other_id}", headers=current).status_code, 204)
        self.assertEqual(self.client.get("/api/users/me", headers=other).status_code, 401)
        self.assertEqual(len(self.client.get("/api/users/me/sessions", headers=current).json()), 1)

    def test_cannot_revoke_another_users_session(self) -> None:
        alice, bob = self.make_user(), self.make_user()
        alice_headers = self.auth(alice)
        bob_headers = self.auth(bob)
        bob_session = self.client.get("/api/users/me/sessions", headers=bob_headers).json()[0]["id"]
        response = self.client.delete(f"/api/users/me/sessions/{bob_session}", headers=alice_headers)
        self.assertEqual(response.status_code, 404)  # same answer as a missing session
        self.assertEqual(self.client.get("/api/users/me", headers=bob_headers).status_code, 200)

"""Forgotten-password flow: generic replies, hashed single-use expiring tokens,
password policy, session invalidation, rate limits and the email backends.

Emails go to a temporary "outbox" folder; nothing is sent anywhere.
"""

import email
import email.policy
import logging
import os
import re
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

from sqlalchemy import select, update

from peerora.constants import MAX_PASSWORD_RESET_EMAILS_PER_ACCOUNT, MAX_PASSWORD_RESET_REQUESTS_PER_IP
from peerora.core.security import hash_token
from peerora.core.timeutils import utcnow
from peerora.models import AuditLog, PasswordResetToken, User
from peerora.services import email_service
from tests.base import CSRF, PASSWORD, ApiTestCase

REQUEST = "/api/auth/password-reset/request"
CONFIRM = "/api/auth/password-reset/confirm"
TOKEN_IN_LINK = re.compile(r"/reset-password#token=([A-Za-z0-9_-]+)")


class ResetTestCase(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.outbox = tempfile.TemporaryDirectory()
        self.addCleanup(self.outbox.cleanup)
        env = mock.patch.dict(os.environ, {
            "EMAIL_BACKEND": "outbox", "EMAIL_OUTBOX_DIR": self.outbox.name,
            "PUBLIC_APP_URL": "https://peerora.example", "VERCEL": "",
            "DATABASE_URL": "sqlite://", "EMAIL_OUTBOX_ALLOW_REMOTE_DB": "",
        })
        env.start()
        self.addCleanup(env.stop)
        self.user = self.make_user(email="sam@example.com", full_name="Sam Student")
        # Capture every log record, to prove tokens are never logged.
        self.records: list[logging.LogRecord] = []
        handler = logging.Handler()
        handler.emit = self.records.append
        root = logging.getLogger()
        root.addHandler(handler)
        previous_level = root.level
        root.setLevel(logging.DEBUG)
        self.addCleanup(root.removeHandler, handler)
        self.addCleanup(root.setLevel, previous_level)

    def emails(self) -> list[str]:
        """Each outbox email as headers + decoded body (as a mail client shows it)."""
        texts = []
        for path in sorted(Path(self.outbox.name).glob("*.eml")):
            message = email.message_from_bytes(path.read_bytes(), policy=email.policy.default)
            texts.append(f"To: {message['To']}\nSubject: {message['Subject']}\n\n{message.get_content()}")
        return texts

    def request(self, email: str = "sam@example.com"):
        return self.client.post(REQUEST, json={"email": email})

    def latest_token(self) -> str:
        match = TOKEN_IN_LINK.search(self.emails()[-1])
        self.assertIsNotNone(match)
        return match.group(1)

    def confirm(self, token: str, password: str = "NewPass456"):
        return self.client.post(CONFIRM, json={"token": token, "new_password": password})


class RequestTests(ResetTestCase):
    def test_existing_and_unknown_emails_get_the_same_reply(self) -> None:
        known = self.request("SAM@example.com")
        unknown = self.request("nobody@example.com")
        self.assertEqual(known.status_code, 202)
        self.assertEqual(unknown.status_code, 202)
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(len(self.emails()), 1)  # only the real account gets an email
        body = self.emails()[0]
        self.assertIn("To: sam@example.com", body)
        self.assertIn("https://peerora.example/reset-password#token=", body)

    def test_token_is_random_hashed_and_time_limited(self) -> None:
        self.request()
        token = self.latest_token()
        self.assertGreaterEqual(len(token), 43)  # 256 bits
        with self.session_factory() as db:
            stored = db.scalar(select(PasswordResetToken))
            self.assertEqual(stored.token_hash, hash_token(token))
            self.assertNotIn(token, stored.token_hash)
            lifetime = stored.expires_at - stored.created_at
            self.assertTrue(timedelta(minutes=29) < lifetime <= timedelta(minutes=31))

    def test_tokens_are_never_logged_or_audited(self) -> None:
        self.request()
        token = self.latest_token()
        self.assertFalse(any(token in record.getMessage() for record in self.records))
        with self.session_factory() as db:
            audit = db.scalars(select(AuditLog)).all()
        self.assertTrue(audit)
        self.assertFalse(any(token in str(log.details) for log in audit))
        self.assertEqual(audit[-1].details["outcome"], "email_queued")

    def test_requesting_again_invalidates_the_older_link(self) -> None:
        self.request()
        first = self.latest_token()
        self.request()
        second = self.latest_token()
        self.assertNotEqual(first, second)
        self.assertEqual(self.confirm(first).status_code, 400)
        self.assertEqual(self.confirm(second).status_code, 200)

    def test_suspended_accounts_get_no_email(self) -> None:
        self.make_user(email="bad@example.com", banned=True)
        reply = self.request("bad@example.com")
        self.assertEqual(reply.status_code, 202)
        self.assertEqual(self.emails(), [])

    def test_invalid_email_is_rejected(self) -> None:
        self.assertEqual(self.client.post(REQUEST, json={"email": "not-an-email"}).status_code, 422)


class ConfirmTests(ResetTestCase):
    def test_successful_reset_changes_password_and_signs_out_everywhere(self) -> None:
        login = self.login("sam@example.com")
        old_access = self.bearer(login)
        self.request()
        reply = self.confirm(self.latest_token())
        self.assertEqual(reply.status_code, 200)
        self.assertIn("log in", reply.json()["detail"])
        # Existing sessions are invalidated: access token and refresh cookie both fail.
        self.assertEqual(self.client.get("/api/users/me", headers=old_access).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/refresh", headers=CSRF).status_code, 401)
        # Old password no longer works, the new one does.
        self.assertEqual(self.login("sam@example.com", PASSWORD).status_code, 401)
        self.assertEqual(self.login("sam@example.com", "NewPass456").status_code, 200)
        with self.session_factory() as db:
            actions = db.scalars(select(AuditLog.action)).all()
        self.assertIn("password_reset_completed", actions)

    def test_token_cannot_be_reused(self) -> None:
        self.request()
        token = self.latest_token()
        self.assertEqual(self.confirm(token).status_code, 200)
        again = self.confirm(token, "OtherPass789")
        self.assertEqual(again.status_code, 400)
        self.assertIn("invalid or has expired", again.json()["detail"])

    def test_expired_token_is_rejected(self) -> None:
        self.request()
        token = self.latest_token()
        with self.session_factory() as db:
            db.execute(update(PasswordResetToken).values(expires_at=utcnow() - timedelta(minutes=1)))
            db.commit()
        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertEqual(self.login("sam@example.com", PASSWORD).status_code, 200)  # password unchanged

    def test_unknown_and_malformed_tokens_are_rejected(self) -> None:
        self.assertEqual(self.confirm("A" * 43).status_code, 400)
        malformed = self.confirm("bad token with spaces!!")
        self.assertEqual(malformed.status_code, 422)
        self.assertIn("invalid or has expired", malformed.text)

    def test_new_password_must_follow_the_policy(self) -> None:
        self.request()
        token = self.latest_token()
        for weak in ("short1", "lettersonly", "12345678", "x" * 129 + "1"):
            with self.subTest(password=weak[:12]):
                self.assertEqual(self.confirm(token, weak).status_code, 422)
        self.assertEqual(self.confirm(token, "SAM@example.com").status_code, 422)  # equals the email
        # Rejected attempts do not use up the link.
        self.assertEqual(self.confirm(token, "StrongPass123").status_code, 200)

    def test_suspended_account_cannot_complete_a_reset(self) -> None:
        self.request()
        token = self.latest_token()
        with self.session_factory() as db:
            user = db.get(User, self.user.id)
            user.is_banned, user.ban_reason = True, "Spam"
            db.commit()
        self.assertEqual(self.confirm(token).status_code, 400)


class EmailChangeTests(ResetTestCase):
    """A reset link sent to an old email address stops working once the address changes."""

    def change_email(self, current_password: str = PASSWORD):
        return self.client.patch("/api/users/me", headers=self.auth(self.user),
                                 json={"email": "sam.new@example.com", "current_password": current_password})

    def test_email_change_retires_only_this_accounts_reset_links(self) -> None:
        self.make_user(email="olivia@example.com")
        self.request("olivia@example.com")
        other_token = self.latest_token()
        self.request()
        own_token = self.latest_token()
        self.assertEqual(self.change_email().status_code, 200)
        self.assertEqual(self.confirm(own_token).status_code, 400)
        # Another account's outstanding link is untouched.
        self.assertEqual(self.confirm(other_token).status_code, 200)
        self.assertEqual(self.login("olivia@example.com", "NewPass456").status_code, 200)

    def test_name_only_change_keeps_the_reset_link(self) -> None:
        self.request()
        token = self.latest_token()
        changed = self.client.patch("/api/users/me", json={"full_name": "Sam S."}, headers=self.auth(self.user))
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(self.confirm(token).status_code, 200)

    def test_refused_email_change_keeps_the_reset_link(self) -> None:
        self.request()
        token = self.latest_token()
        self.assertEqual(self.change_email(current_password="WrongPass999").status_code, 400)
        self.assertEqual(self.confirm(token).status_code, 200)


class RateLimitTests(ResetTestCase):
    def test_requests_are_limited_per_address(self) -> None:
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_IP):
            self.assertEqual(self.request("nobody@example.com").status_code, 202)
        blocked = self.request("sam@example.com")
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked.headers)

    def test_one_account_cannot_be_flooded_with_emails(self) -> None:
        with mock.patch.dict(os.environ, {"TRUST_PROXY_HEADERS": "true"}):
            for index in range(MAX_PASSWORD_RESET_EMAILS_PER_ACCOUNT + 2):
                reply = self.client.post(REQUEST, json={"email": "sam@example.com"},
                                         headers={"X-Forwarded-For": f"203.0.113.{index + 1}"})
                self.assertEqual(reply.status_code, 202)  # same generic reply every time
        self.assertEqual(len(self.emails()), MAX_PASSWORD_RESET_EMAILS_PER_ACCOUNT)


class EmailConfigurationTests(ResetTestCase):
    def test_reset_is_unavailable_without_an_email_backend(self) -> None:
        with mock.patch.dict(os.environ, {"EMAIL_BACKEND": ""}):
            availability = self.client.get("/api/auth/password-reset/availability").json()
            self.assertFalse(availability["available"])
            # Same answer for every email: no enumeration, and no pretending.
            self.assertEqual(self.request("sam@example.com").status_code, 503)
            self.assertEqual(self.request("nobody@example.com").status_code, 503)
        self.assertTrue(self.client.get("/api/auth/password-reset/availability").json()["available"])

    def test_outbox_backend_is_refused_on_vercel(self) -> None:
        with mock.patch.dict(os.environ, {"VERCEL": "1"}):
            self.assertIn("disabled on Vercel", email_service.configuration_problem())
            self.assertEqual(self.request().status_code, 503)
        self.assertEqual(self.emails(), [])

    def test_outbox_backend_is_refused_with_a_remote_database(self) -> None:
        # Only the environment variable changes; the test database stays SQLite.
        remote = {"DATABASE_URL": "postgresql://user@db.example.com/postgres"}
        with mock.patch.dict(os.environ, remote):
            self.assertIn("local SQLite database", email_service.configuration_problem())
            self.assertFalse(self.client.get("/api/auth/password-reset/availability").json()["available"])
            self.assertEqual(self.request().status_code, 503)
        self.assertEqual(self.emails(), [])
        with self.session_factory() as db:
            self.assertEqual(db.scalars(select(PasswordResetToken)).all(), [])

    def test_outbox_with_a_remote_database_can_be_allowed_on_purpose(self) -> None:
        allowed = {"DATABASE_URL": "postgresql://user@db.example.com/postgres",
                   "EMAIL_OUTBOX_ALLOW_REMOTE_DB": "true"}
        with mock.patch.dict(os.environ, allowed):
            self.assertIsNone(email_service.configuration_problem())

    def test_smtp_requires_host_and_sender(self) -> None:
        with mock.patch.dict(os.environ, {"EMAIL_BACKEND": "smtp", "SMTP_HOST": "", "EMAIL_FROM": ""}):
            problem = email_service.configuration_problem()
        self.assertIn("SMTP_HOST", problem)
        self.assertIn("EMAIL_FROM", problem)

    def test_smtp_backend_sends_with_starttls_and_login(self) -> None:
        settings = {"EMAIL_BACKEND": "smtp", "SMTP_HOST": "smtp.example.com", "SMTP_PORT": "587",
                    "SMTP_USERNAME": "mailer", "SMTP_PASSWORD": "not-a-real-password",
                    "EMAIL_FROM": "Peerora <no-reply@peerora.example>"}
        with mock.patch.dict(os.environ, settings), mock.patch("smtplib.SMTP") as smtp:
            server = smtp.return_value.__enter__.return_value
            self.assertEqual(self.request().status_code, 202)
        smtp.assert_called_once_with("smtp.example.com", 587, timeout=15)
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("mailer", "not-a-real-password")
        sent = server.send_message.call_args.args[0]
        self.assertEqual(sent["To"], "sam@example.com")
        self.assertIn("/reset-password#token=", sent.get_content())

    def test_delivery_failure_is_logged_without_details(self) -> None:
        settings = {"EMAIL_BACKEND": "smtp", "SMTP_HOST": "smtp.example.com", "EMAIL_FROM": "x@peerora.example"}
        with mock.patch.dict(os.environ, settings), mock.patch("smtplib.SMTP", side_effect=OSError("boom sam@example.com")):
            self.assertEqual(self.request().status_code, 202)  # the reply never reveals delivery problems
        warnings = [r.getMessage() for r in self.records if r.name == "peerora.password_reset"]
        self.assertTrue(any("could not be delivered (OSError)" in message for message in warnings))
        self.assertFalse(any("sam@example.com" in message or "token" in message.lower() for message in warnings))

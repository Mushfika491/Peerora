"""Signup, login, logout, password hashing, password rules and password change."""

from sqlalchemy import select

from peerora.config import REFRESH_COOKIE_NAME
from peerora.core.security import verify_password
from peerora.models import AuditLog, LoginAttempt, User
from tests.base import CSRF, PASSWORD, ApiTestCase


def signup_body(**changes):
    body = {"full_name": "New Student", "email": "New@Example.com", "password": "GoodPass123",
            "account_type": "student"}
    body.update(changes)
    return body


class SignupTests(ApiTestCase):
    def test_signup_creates_user_role_and_signs_in(self) -> None:
        response = self.client.post("/api/auth/signup", json=signup_body())
        self.assertEqual(response.status_code, 201, response.text)
        data = response.json()
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["expires_in"], 15 * 60)
        self.assertEqual(data["user"]["email"], "new@example.com")  # stored lowercase
        self.assertEqual(data["user"]["role"], "user")
        self.assertEqual(data["user"]["account_type"], "student")
        self.assertNotIn("password_hash", data["user"])
        # The refresh token is only in an HttpOnly cookie, never in the body.
        self.assertNotIn("refresh_token", data)
        cookie = response.headers["set-cookie"]
        self.assertIn(f"{REFRESH_COOKIE_NAME}=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Path=/api/auth", cookie)
        self.assertIn("SameSite=strict", cookie)

    def test_tutor_signup(self) -> None:
        response = self.client.post("/api/auth/signup", json=signup_body(account_type="tutor"))
        self.assertEqual(response.json()["user"]["account_type"], "tutor")

    def test_password_is_hashed_with_argon2_and_pepper(self) -> None:
        self.client.post("/api/auth/signup", json=signup_body())
        with self.session_factory() as db:
            user = db.scalar(select(User).where(User.email == "new@example.com"))
        self.assertNotIn("GoodPass123", user.password_hash)
        self.assertTrue(user.password_hash.startswith("$argon2id$"))
        self.assertTrue(verify_password("GoodPass123", user.password_hash))
        self.assertFalse(verify_password("WrongPass123", user.password_hash))

    def test_admin_cannot_be_chosen_at_signup(self) -> None:
        as_admin_type = self.client.post("/api/auth/signup", json=signup_body(account_type="admin"))
        self.assertEqual(as_admin_type.status_code, 422)
        with_role = self.client.post("/api/auth/signup", json=signup_body(role="admin"))
        self.assertEqual(with_role.status_code, 422)
        self.assertIn("is not an accepted field", with_role.text)
        with self.session_factory() as db:
            self.assertEqual(db.scalar(select(User).where(User.role == "admin")), None)

    def test_duplicate_email_is_case_insensitive(self) -> None:
        self.assertEqual(self.client.post("/api/auth/signup", json=signup_body()).status_code, 201)
        again = self.client.post("/api/auth/signup", json=signup_body(email="NEW@example.COM"))
        self.assertEqual(again.status_code, 409)

    def test_password_rules_are_enforced_on_the_backend(self) -> None:
        for password in ("short1", "lettersonly", "12345678", "x" * 129 + "1"):
            with self.subTest(password=password[:12]):
                response = self.client.post("/api/auth/signup", json=signup_body(password=password))
                self.assertEqual(response.status_code, 422)
        same_as_email = self.client.post(
            "/api/auth/signup", json=signup_body(email="abc12345@x.io", password="abc12345@x.io")
        )
        self.assertEqual(same_as_email.status_code, 422)

    def test_invalid_email_and_name(self) -> None:
        self.assertEqual(self.client.post("/api/auth/signup", json=signup_body(email="nope")).status_code, 422)
        self.assertEqual(self.client.post("/api/auth/signup", json=signup_body(full_name="A")).status_code, 422)


class LoginTests(ApiTestCase):
    def test_login_success_records_attempt_and_audit(self) -> None:
        user = self.make_user(email="sam@example.com")
        response = self.login("SAM@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], user.id)
        me = self.client.get("/api/users/me", headers=self.bearer(response))
        self.assertEqual(me.json()["email"], "sam@example.com")
        with self.session_factory() as db:
            attempt = db.scalar(select(LoginAttempt))
            self.assertTrue(attempt.success)
            actions = db.scalars(select(AuditLog.action)).all()
            self.assertIn("login_success", actions)

    def test_wrong_password_and_unknown_email_look_the_same(self) -> None:
        self.make_user(email="sam@example.com")
        wrong = self.login("sam@example.com", "WrongPass123")
        unknown = self.login("nobody@example.com", "WrongPass123")
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(wrong.json(), unknown.json())
        self.assertNotIn("set-cookie", wrong.headers)
        with self.session_factory() as db:
            failures = db.scalars(select(LoginAttempt).where(LoginAttempt.success.is_(False))).all()
            self.assertEqual(len(failures), 2)
            self.assertEqual({f.failure_reason for f in failures}, {"bad_credentials"})
            logged = db.scalars(select(AuditLog).where(AuditLog.action == "login_failed")).all()
            self.assertEqual(len(logged), 2)
            # Failed-login details never contain the attempted password.
            self.assertNotIn("WrongPass123", str([log.details for log in logged]))

    def test_banned_user_cannot_log_in(self) -> None:
        self.make_user(email="bad@example.com", banned=True)
        response = self.login("bad@example.com")
        self.assertEqual(response.status_code, 403)
        self.assertIn("suspended", response.json()["detail"])

    def test_logout_revokes_the_session(self) -> None:
        self.make_user(email="sam@example.com")
        login = self.login("sam@example.com")
        headers = self.bearer(login)
        self.assertEqual(self.client.post("/api/auth/logout", headers=CSRF).status_code, 204)
        # The refresh cookie no longer works...
        self.assertEqual(self.client.post("/api/auth/refresh", headers=CSRF).status_code, 401)
        # ...and neither does the access token of that session.
        self.assertEqual(self.client.get("/api/users/me", headers=headers).status_code, 401)
        with self.session_factory() as db:
            self.assertIn("logout", db.scalars(select(AuditLog.action)).all())

    def test_logout_and_refresh_require_the_csrf_header(self) -> None:
        self.make_user(email="sam@example.com")
        self.login("sam@example.com")
        self.assertEqual(self.client.post("/api/auth/refresh").status_code, 403)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 403)


class PasswordChangeTests(ApiTestCase):
    def test_change_password_requires_current_password(self) -> None:
        user = self.make_user(email="sam@example.com")
        headers = self.auth(user)
        wrong = self.client.post("/api/users/me/password", headers=headers,
                                 json={"current_password": "WrongPass123", "new_password": "NewPass456"})
        self.assertEqual(wrong.status_code, 400)
        weak = self.client.post("/api/users/me/password", headers=headers,
                                json={"current_password": PASSWORD, "new_password": "weak"})
        self.assertEqual(weak.status_code, 422)

    def test_change_password_signs_out_other_sessions(self) -> None:
        user = self.make_user(email="sam@example.com")
        this_device = self.auth(user)
        other_device = self.auth(user)
        response = self.client.post("/api/users/me/password", headers=this_device,
                                    json={"current_password": PASSWORD, "new_password": "NewPass456"})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get("/api/users/me", headers=this_device).status_code, 200)
        self.assertEqual(self.client.get("/api/users/me", headers=other_device).status_code, 401)
        self.assertEqual(self.login("sam@example.com").status_code, 401)
        self.assertEqual(self.login("sam@example.com", "NewPass456").status_code, 200)
        with self.session_factory() as db:
            self.assertIn("password_changed", db.scalars(select(AuditLog.action)).all())


class ProfileTests(ApiTestCase):
    def test_update_name_and_email(self) -> None:
        user = self.make_user(email="sam@example.com")
        headers = self.auth(user)
        renamed = self.client.patch("/api/users/me", headers=headers, json={"full_name": "Samira Rahman"})
        self.assertEqual(renamed.json()["full_name"], "Samira Rahman")
        no_password = self.client.patch("/api/users/me", headers=headers, json={"email": "new@example.com"})
        self.assertEqual(no_password.status_code, 400)
        changed = self.client.patch("/api/users/me", headers=headers,
                                    json={"email": "New@example.com", "current_password": PASSWORD})
        self.assertEqual(changed.json()["email"], "new@example.com")

    def test_role_and_account_type_cannot_be_changed_by_the_user(self) -> None:
        headers = self.auth(self.make_user())
        for field, value in (("role", "admin"), ("account_type", "tutor")):
            with self.subTest(field=field):
                response = self.client.patch("/api/users/me", headers=headers, json={field: value})
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/api/users/me", headers=headers).json()["role"], "user")

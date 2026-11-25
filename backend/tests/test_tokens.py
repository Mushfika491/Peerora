"""Access-token (JWT) validation: missing, invalid, tampered, expired, stale role."""

import base64
import json
from datetime import timedelta

import jwt

from peerora.config import JWT_ALGORITHM, get_jwt_secret
from peerora.core.security import create_access_token
from peerora.models import User
from tests.base import ApiTestCase

PROTECTED = "/api/users/me"


class AccessTokenTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = self.make_user()
        self.headers = self.auth(self.user)
        self.session_id = jwt.decode(self.headers["Authorization"][7:], options={"verify_signature": False})["sid"]

    def get(self, token: str | None):
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        return self.client.get(PROTECTED, headers=headers)

    def test_valid_token_is_accepted(self) -> None:
        self.assertEqual(self.client.get(PROTECTED, headers=self.headers).status_code, 200)

    def test_token_contains_user_id_role_and_session(self) -> None:
        claims = jwt.decode(self.headers["Authorization"][7:], get_jwt_secret(), algorithms=[JWT_ALGORITHM],
                            issuer="peerora")
        self.assertEqual(claims["sub"], str(self.user.id))
        self.assertEqual(claims["role"], "user")
        self.assertEqual(claims["type"], "access")
        self.assertLessEqual(claims["exp"] - claims["iat"], 15 * 60)

    def test_missing_token_returns_401(self) -> None:
        response = self.get(None)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_garbage_token_returns_401(self) -> None:
        self.assertEqual(self.get("not-a-jwt").status_code, 401)

    def test_tampered_token_returns_401(self) -> None:
        header, payload, signature = self.headers["Authorization"][7:].split(".")
        claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
        claims["role"] = "admin"  # try to become an administrator
        forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
        self.assertEqual(self.get(f"{header}.{forged}.{signature}").status_code, 401)

    def test_token_signed_with_another_key_returns_401(self) -> None:
        token = jwt.encode({"sub": str(self.user.id), "role": "admin", "sid": self.session_id, "type": "access",
                            "iss": "peerora", "iat": 0, "exp": 9999999999}, "another-key-" * 4, algorithm="HS256")
        self.assertEqual(self.get(token).status_code, 401)

    def test_unsigned_none_algorithm_token_returns_401(self) -> None:
        token = jwt.encode({"sub": str(self.user.id), "role": "user", "sid": self.session_id, "type": "access",
                            "iss": "peerora", "iat": 0, "exp": 9999999999}, None, algorithm="none")
        self.assertEqual(self.get(token).status_code, 401)

    def test_expired_token_returns_401(self) -> None:
        token = create_access_token(self.user.id, "user", self.session_id, lifetime=timedelta(seconds=-5))
        response = self.get(token)
        self.assertEqual(response.status_code, 401)
        self.assertIn("expired", response.json()["detail"])

    def test_token_for_revoked_session_returns_401(self) -> None:
        self.client.delete(f"/api/users/me/sessions/{self.session_id}", headers=self.headers)
        self.assertEqual(self.client.get(PROTECTED, headers=self.headers).status_code, 401)

    def test_token_with_outdated_role_returns_401(self) -> None:
        with self.session_factory() as db:
            db.get(User, self.user.id).role = "admin"
            db.commit()
        self.assertEqual(self.client.get(PROTECTED, headers=self.headers).status_code, 401)

    def test_banned_user_is_rejected_on_next_request(self) -> None:
        with self.session_factory() as db:
            user = db.get(User, self.user.id)
            user.is_banned = True
            user.ban_reason = "Spam"
            db.commit()
        response = self.client.get(PROTECTED, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("suspended", response.json()["detail"])

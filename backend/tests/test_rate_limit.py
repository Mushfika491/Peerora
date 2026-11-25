"""Brute-force protection on login and rate limiting on signup.

Login failures are counted per (account, IP address), per IP address, and
(with a much higher limit) per account. The tests use X-Forwarded-For with
TRUST_PROXY_HEADERS enabled to simulate requests from different networks.
"""

import os
from unittest import mock

from sqlalchemy import select

from peerora.constants import (
    MAX_FAILED_LOGINS_PER_ACCOUNT,
    MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP,
    MAX_FAILED_LOGINS_PER_IP,
    MAX_SIGNUPS_PER_IP,
)
from peerora.models import LoginAttempt
from tests.base import PASSWORD, ApiTestCase


class ThrottleTestCase(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        patcher = mock.patch.dict(os.environ, {"TRUST_PROXY_HEADERS": "true"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def login_from(self, ip: str, email: str, password: str = PASSWORD):
        return self.client.post("/api/auth/login", json={"email": email, "password": password},
                                headers={"X-Forwarded-For": ip})


class LoginThrottleTests(ThrottleTestCase):
    def test_account_is_throttled_from_the_attacking_address(self) -> None:
        self.make_user(email="target@example.com")
        for _ in range(MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP):
            self.assertEqual(self.login_from("203.0.113.9", "target@example.com", "WrongPass123").status_code, 401)
        # Even the correct password is refused from that address while throttled.
        blocked = self.login_from("203.0.113.9", "target@example.com")
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked.headers)
        with self.session_factory() as db:
            self.assertIn("throttled", db.scalars(select(LoginAttempt.failure_reason)).all())

    def test_owner_can_still_log_in_from_another_network(self) -> None:
        """Someone typing your email cannot lock you out (lockout denial of service)."""
        self.make_user(email="target@example.com")
        for _ in range(MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP + 3):
            self.login_from("203.0.113.9", "target@example.com", "WrongPass123")
        self.assertEqual(self.login_from("198.51.100.7", "target@example.com").status_code, 200)

    def test_hammering_while_throttled_does_not_build_a_global_lockout(self) -> None:
        self.make_user(email="target@example.com")
        for _ in range(MAX_FAILED_LOGINS_PER_ACCOUNT + 5):  # mostly refused as "throttled"
            self.login_from("203.0.113.9", "target@example.com", "WrongPass123")
        self.assertEqual(self.login_from("198.51.100.7", "target@example.com").status_code, 200)

    def test_one_address_cannot_guess_many_accounts(self) -> None:
        for number in range(MAX_FAILED_LOGINS_PER_IP):
            self.login_from("203.0.113.9", f"guess{number}@example.com", "WrongPass123")
        self.make_user(email="innocent@example.com")
        self.assertEqual(self.login_from("203.0.113.9", "innocent@example.com").status_code, 429)
        self.assertEqual(self.login_from("198.51.100.7", "innocent@example.com").status_code, 200)

    def test_guessing_spread_over_many_addresses_is_capped_per_account(self) -> None:
        self.make_user(email="target@example.com")
        guesses_per_address = MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP
        addresses = -(-MAX_FAILED_LOGINS_PER_ACCOUNT // guesses_per_address)  # ceiling division
        for index in range(addresses):
            for _ in range(guesses_per_address):
                self.login_from(f"10.0.{index // 250}.{index % 250 + 1}", "target@example.com", "WrongPass123")
        self.assertEqual(self.login_from("198.51.100.7", "target@example.com").status_code, 429)

    def test_other_accounts_are_not_affected(self) -> None:
        self.make_user(email="target@example.com")
        self.make_user(email="other@example.com")
        for _ in range(MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP):
            self.login_from("203.0.113.9", "target@example.com", "WrongPass123")
        self.assertEqual(self.login_from("203.0.113.9", "other@example.com").status_code, 200)


class SignupRateLimitTests(ThrottleTestCase):
    def signup_from(self, ip: str, number: int):
        return self.client.post(
            "/api/auth/signup",
            json={"full_name": "New User", "email": f"new{number}@example.com", "password": "GoodPass123",
                  "account_type": "student"},
            headers={"X-Forwarded-For": ip},
        )

    def test_signups_are_limited_per_address(self) -> None:
        for number in range(MAX_SIGNUPS_PER_IP):
            self.assertEqual(self.signup_from("203.0.113.9", number).status_code, 201)
        blocked = self.signup_from("203.0.113.9", 999)
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked.headers)
        # Another network is not affected.
        self.assertEqual(self.signup_from("198.51.100.7", 1000).status_code, 201)

    def test_failed_signups_do_not_count(self) -> None:
        for _ in range(MAX_SIGNUPS_PER_IP + 2):
            duplicate = self.client.post(
                "/api/auth/signup",
                json={"full_name": "Bad", "email": "x", "password": "short", "account_type": "student"},
                headers={"X-Forwarded-For": "203.0.113.9"},
            )
            self.assertEqual(duplicate.status_code, 422)
        self.assertEqual(self.signup_from("203.0.113.9", 1).status_code, 201)

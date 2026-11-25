"""Audit log contents, sanitisation, search and the failed-login report."""

import csv
import io

from sqlalchemy import select

from peerora.core.request_info import ClientInfo
from peerora.models import AuditLog
from peerora.services.audit_service import AuditAction, log_event, sanitize
from tests.base import ApiTestCase


class AuditLogTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin_h = self.auth(self.make_user(role="admin"))
        self.user = self.make_user(email="sam@example.com")

    def test_sensitive_keys_are_never_stored(self) -> None:
        clean = sanitize({"reason": "spam", "password": "x", "new_password": "y", "access_token": "z",
                          "nested": {"refresh_token": "t", "ok": 1}})
        self.assertEqual(clean, {"reason": "spam", "nested": {"ok": 1}})
        with self.session_factory() as db:
            log_event(db, AuditAction.EXPORT, ClientInfo("1.2.3.4", "agent"), details={"password_hash": "h", "rows": 1})
            db.commit()
            stored = db.scalar(select(AuditLog))
            self.assertEqual(stored.details, {"rows": 1})

    def test_login_events_record_ip_user_agent_and_time(self) -> None:
        self.client.post("/api/auth/login", json={"email": "sam@example.com", "password": "WrongPass123"},
                         headers={"User-Agent": "TestBrowser/1.0"})
        logs = self.client.get("/api/admin/audit-logs?action=login_failed", headers=self.admin_h).json()["items"]
        self.assertEqual(len(logs), 1)
        log = logs[0]
        self.assertEqual(log["target_user_email"], "sam@example.com")
        self.assertEqual(log["user_agent"], "TestBrowser/1.0")
        self.assertIsNotNone(log["ip_address"])
        self.assertIsNotNone(log["created_at"])
        self.assertNotIn("WrongPass123", str(log))

    def test_search_and_user_filter(self) -> None:
        self.login("sam@example.com")
        by_user = self.client.get(f"/api/admin/audit-logs?user_id={self.user.id}", headers=self.admin_h).json()
        self.assertEqual({item["action"] for item in by_user["items"]}, {"login_success"})
        by_text = self.client.get("/api/admin/audit-logs?q=login_succ", headers=self.admin_h).json()
        self.assertEqual(by_text["total"], 1)
        actions = self.client.get("/api/admin/audit-actions", headers=self.admin_h).json()
        self.assertIn("user_banned", actions)

    def test_text_search_matches_user_emails_and_keeps_filters(self) -> None:
        other = self.make_user(email="zara@example.com")
        self.login("sam@example.com")
        self.login("zara@example.com")
        self.login("zara@example.com", "WrongPass123")

        def search(query: str) -> list[tuple[str, str | None]]:
            items = self.client.get(f"/api/admin/audit-logs{query}", headers=self.admin_h).json()["items"]
            return sorted((i["action"], i["actor_email"] or i["target_user_email"]) for i in items)

        # Matches the actor's email (successful login) and the target's email (failed login).
        self.assertEqual(search("?q=ZARA@"), [("login_failed", "zara@example.com"), ("login_success", "zara@example.com")])
        # Combined with the existing filters.
        self.assertEqual(search("?q=zara&action=login_failed"), [("login_failed", "zara@example.com")])
        self.assertEqual(search(f"?q=zara&user_id={other.id}&action=login_success"),
                         [("login_success", "zara@example.com")])
        self.assertEqual(search(f"?q=sam&user_id={other.id}"), [])
        # Searching the details text works too (the failed-login reason).
        self.assertEqual(search("?q=bad_credentials"), [("login_failed", "zara@example.com")])
        # Exports use the same search.
        csv_text = self.client.get("/api/admin/exports/audit-logs.csv?q=zara", headers=self.admin_h).text
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        self.assertEqual(sorted(row["action"] for row in rows), ["login_failed", "login_success"])
        self.assertNotIn("sam@example.com", csv_text)

    def test_failed_login_report_groups_by_ip_and_account(self) -> None:
        for _ in range(3):
            self.login("sam@example.com", "WrongPass123")
        self.login("ghost@example.com", "WrongPass123")
        report = self.client.get("/api/admin/security/failed-logins?hours=24", headers=self.admin_h).json()
        self.assertEqual(report["total_failures"], 4)
        by_account = {row["key"]: row["failures"] for row in report["by_account"]}
        self.assertEqual(by_account, {"sam@example.com": 3, "ghost@example.com": 1})
        self.assertEqual(report["by_ip"][0]["failures"], 4)
        self.assertEqual(len(report["recent"]), 4)

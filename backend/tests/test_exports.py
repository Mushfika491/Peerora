"""CSV exports: admin only, filter-aware, audited and safe against CSV injection."""

import csv
import io

from sqlalchemy import select

from peerora.models import AuditLog
from peerora.services.export_service import safe_cell
from tests.base import ApiTestCase


def parse(response) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(response.text)))


class ExportTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin_h = self.auth(self.make_user(role="admin", email="admin@example.com"))
        self.make_user(email="student@example.com")
        self.make_user("tutor", email="tutor@example.com", full_name="=HYPERLINK(\"http://evil\")")

    def test_users_export_respects_filters(self) -> None:
        response = self.client.get("/api/admin/exports/users.csv?account_type=tutor", headers=self.admin_h)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["content-type"])
        self.assertIn("attachment; filename=", response.headers["content-disposition"])
        rows = parse(response)
        self.assertEqual([row["email"] for row in rows], ["tutor@example.com"])
        self.assertNotIn("password_hash", response.text)

    def test_formula_cells_are_escaped(self) -> None:
        rows = parse(self.client.get("/api/admin/exports/users.csv?q=tutor@", headers=self.admin_h))
        self.assertTrue(rows[0]["full_name"].startswith("'="))
        self.assertEqual(safe_cell("-1+2"), "'-1+2")
        self.assertEqual(safe_cell("normal"), "normal")
        self.assertEqual(safe_cell(None), "")

    def test_records_and_audit_exports(self) -> None:
        owner_h = self.auth(self.make_user(email="owner@example.com"))
        self.client.post("/api/records", json={"title": "Done item", "status": "done"}, headers=owner_h)
        self.client.post("/api/records", json={"title": "Open item"}, headers=owner_h)
        records = parse(self.client.get("/api/admin/exports/records.csv?status=done", headers=self.admin_h))
        self.assertEqual([row["title"] for row in records], ["Done item"])

        self.login("student@example.com", "WrongPass123")
        logs = parse(self.client.get("/api/admin/exports/audit-logs.csv?action=login_failed", headers=self.admin_h))
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "login_failed")

    def test_exports_are_audited(self) -> None:
        self.client.get("/api/admin/exports/users.csv?role=user", headers=self.admin_h)
        with self.session_factory() as db:
            export = db.scalar(select(AuditLog).where(AuditLog.action == "export"))
        self.assertEqual(export.details["export"], "users")
        self.assertEqual(export.details["filters"], {"role": "user"})
        self.assertEqual(export.details["rows"], 2)

    def test_exports_are_admin_only(self) -> None:
        user_h = self.auth(self.make_user())
        for kind in ("users", "records", "audit-logs"):
            with self.subTest(kind=kind):
                self.assertEqual(self.client.get(f"/api/admin/exports/{kind}.csv", headers=user_h).status_code, 403)
                self.assertEqual(self.client.get(f"/api/admin/exports/{kind}.csv").status_code, 401)

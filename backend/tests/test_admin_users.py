"""Admin user management and the administrator restrictions."""

from sqlalchemy import select

from peerora.models import AuditLog, User
from tests.base import ApiTestCase


class AdminUserTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_user(role="admin", email="admin1@example.com", full_name="Ada Admin")
        self.other_admin = self.make_user("tutor", role="admin", email="admin2@example.com", full_name="Tom Admin")
        self.student = self.make_user(email="student@example.com", full_name="Sam Student")
        self.tutor = self.make_user("tutor", email="tutor@example.com", full_name="Tina Tutor")
        self.h = self.auth(self.admin)

    def audit_actions(self) -> list[str]:
        with self.session_factory() as db:
            return list(db.scalars(select(AuditLog.action)).all())

    def test_overview_counts(self) -> None:
        data = self.client.get("/api/admin/overview", headers=self.h).json()
        self.assertEqual(data["total_users"], 4)
        self.assertEqual(data["admin_users"], 2)
        self.assertEqual(data["banned_users"], 0)
        self.assertEqual(data["new_users_last_7_days"], 4)
        for key in ("total_records", "total_groups", "total_tutor_profiles"):
            self.assertEqual(data[key], 0)

    def test_search_filters_and_pagination(self) -> None:
        def emails(query: str) -> list[str]:
            body = self.client.get(f"/api/admin/users{query}", headers=self.h).json()
            return sorted(item["email"] for item in body["items"])

        self.assertEqual(emails("?q=tina"), ["tutor@example.com"])
        self.assertEqual(emails("?role=admin"), ["admin1@example.com", "admin2@example.com"])
        self.assertEqual(emails("?account_type=tutor&role=user"), ["tutor@example.com"])
        page = self.client.get("/api/admin/users?page=2&page_size=3", headers=self.h).json()
        self.assertEqual((page["total"], page["page"], len(page["items"])), (4, 2, 1))
        self.assertEqual(self.client.get("/api/admin/users?status=nonsense", headers=self.h).status_code, 422)

    def test_user_detail_contains_sessions_and_activity(self) -> None:
        self.login("student@example.com")
        detail = self.client.get(f"/api/admin/users/{self.student.id}", headers=self.h).json()
        self.assertEqual(detail["user"]["email"], "student@example.com")
        self.assertEqual(len(detail["active_sessions"]), 1)
        self.assertIn("login_success", [log["action"] for log in detail["recent_activity"]])
        self.assertNotIn("password_hash", str(detail))
        self.assertEqual(self.client.get("/api/admin/users/9999", headers=self.h).status_code, 404)

    def test_ban_requires_reason_revokes_sessions_and_is_audited(self) -> None:
        student_headers = self.auth(self.student)
        no_reason = self.client.post(f"/api/admin/users/{self.student.id}/ban", json={}, headers=self.h)
        self.assertEqual(no_reason.status_code, 422)
        banned = self.client.post(f"/api/admin/users/{self.student.id}/ban", json={"reason": "Spamming groups"},
                                  headers=self.h)
        self.assertEqual(banned.status_code, 200)
        self.assertTrue(banned.json()["is_banned"])
        self.assertEqual(banned.json()["ban_reason"], "Spamming groups")
        # The banned user's live token is rejected on the next request.
        self.assertEqual(self.client.get("/api/users/me", headers=student_headers).status_code, 403)
        self.assertEqual(self.login("student@example.com").status_code, 403)
        self.assertIn("user_banned", self.audit_actions())

        unbanned = self.client.post(f"/api/admin/users/{self.student.id}/unban", json={"reason": "Appeal accepted"},
                                    headers=self.h)
        self.assertFalse(unbanned.json()["is_banned"])
        self.assertEqual(self.login("student@example.com").status_code, 200)
        self.assertIn("user_unbanned", self.audit_actions())

    def test_admin_cannot_ban_another_admin_or_themself(self) -> None:
        other = self.client.post(f"/api/admin/users/{self.other_admin.id}/ban", json={"reason": "Test reason"}, headers=self.h)
        self.assertEqual(other.status_code, 403)
        me = self.client.post(f"/api/admin/users/{self.admin.id}/ban", json={"reason": "Test reason"}, headers=self.h)
        self.assertEqual(me.status_code, 403)

    def test_admin_cannot_change_own_role(self) -> None:
        response = self.client.patch(f"/api/admin/users/{self.admin.id}/role", json={"role": "user"}, headers=self.h)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.db_get(User, self.admin.id).role, "admin")

    def test_role_change_takes_effect_immediately(self) -> None:
        student_headers = self.auth(self.student)
        promoted = self.client.patch(f"/api/admin/users/{self.student.id}/role", json={"role": "admin"}, headers=self.h)
        self.assertEqual(promoted.json()["role"], "admin")
        self.assertEqual(self.db_get(User, self.student.id).account_type, "student")  # account type unchanged
        # The old token carries the old role and is refused; a new login works as admin.
        self.assertEqual(self.client.get("/api/users/me", headers=student_headers).status_code, 401)
        new_headers = self.bearer(self.login("student@example.com"))
        self.assertEqual(self.client.get("/api/admin/overview", headers=new_headers).status_code, 200)
        self.assertIn("role_changed", self.audit_actions())

    def test_bulk_ban_skips_admins_and_self(self) -> None:
        response = self.client.post("/api/admin/users/bulk-ban", headers=self.h, json={
            "user_ids": [self.student.id, self.tutor.id, self.other_admin.id, self.admin.id, 9999],
            "reason": "Bulk moderation",
        })
        results = {item["id"]: item["result"] for item in response.json()["results"]}
        self.assertEqual(response.json()["done"], 2)
        self.assertEqual(results[self.other_admin.id], "skipped_admin")
        self.assertEqual(results[self.admin.id], "skipped_self")
        self.assertEqual(results[9999], "not_found")
        self.assertTrue(self.db_get(User, self.tutor.id).is_banned)

        no_reason = self.client.post("/api/admin/users/bulk-unban", headers=self.h,
                                     json={"user_ids": [self.student.id, self.tutor.id]})
        self.assertEqual(no_reason.status_code, 422)
        unban = self.client.post("/api/admin/users/bulk-unban", headers=self.h,
                                 json={"user_ids": [self.student.id, self.tutor.id], "reason": "Appeal accepted"})
        self.assertEqual(unban.json()["done"], 2)
        with self.session_factory() as db:
            logged = db.scalars(select(AuditLog).where(AuditLog.action == "user_unbanned")).all()
        self.assertEqual({log.details["reason"] for log in logged}, {"Appeal accepted"})

    def test_unban_reason_is_required(self) -> None:
        self.client.post(f"/api/admin/users/{self.student.id}/ban", json={"reason": "Spam"}, headers=self.h)
        url = f"/api/admin/users/{self.student.id}/unban"
        for name, body in (("missing", {}), ("empty", {"reason": ""}), ("blank", {"reason": "   "}),
                           ("too short", {"reason": "ok"}), ("too long", {"reason": "x" * 501})):
            with self.subTest(name):
                self.assertEqual(self.client.post(url, json=body, headers=self.h).status_code, 422)
        self.assertTrue(self.db_get(User, self.student.id).is_banned)
        valid = self.client.post(url, json={"reason": "  Appeal accepted  "}, headers=self.h)
        self.assertEqual(valid.status_code, 200)
        self.assertFalse(valid.json()["is_banned"])
        with self.session_factory() as db:
            log = db.scalar(select(AuditLog).where(AuditLog.action == "user_unbanned"))
        self.assertEqual(log.details["reason"], "Appeal accepted")  # stored, trimmed
        self.assertEqual(log.details["previous_ban_reason"], "Spam")

    def test_suspended_responses_are_tagged_for_the_frontend(self) -> None:
        student_headers = self.auth(self.student)
        self.client.post(f"/api/admin/users/{self.student.id}/ban", json={"reason": "Spam"}, headers=self.h)
        suspended = self.client.get("/api/users/me", headers=student_headers)
        self.assertEqual(suspended.status_code, 403)
        self.assertEqual(suspended.headers.get("x-error-code"), "account_suspended")
        login = self.login("student@example.com")
        self.assertEqual(login.headers.get("x-error-code"), "account_suspended")
        # An ordinary permission error is NOT tagged, so it never signs the user out.
        ordinary = self.client.get("/api/admin/overview", headers=self.auth(self.tutor))
        self.assertEqual(ordinary.status_code, 403)
        self.assertIsNone(ordinary.headers.get("x-error-code"))

    def test_admin_session_revocation(self) -> None:
        student_headers = self.auth(self.student)
        detail = self.client.get(f"/api/admin/users/{self.student.id}", headers=self.h).json()
        session_id = detail["active_sessions"][0]["id"]
        wrong_user = self.client.delete(f"/api/admin/users/{self.tutor.id}/sessions/{session_id}", headers=self.h)
        self.assertEqual(wrong_user.status_code, 404)
        ok = self.client.delete(f"/api/admin/users/{self.student.id}/sessions/{session_id}", headers=self.h)
        self.assertEqual(ok.status_code, 204)
        self.assertEqual(self.client.get("/api/users/me", headers=student_headers).status_code, 401)

        self.auth(self.student)
        self.auth(self.student)
        revoked = self.client.post(f"/api/admin/users/{self.student.id}/sessions/revoke-all", headers=self.h)
        self.assertEqual(revoked.json()["revoked"], 2)

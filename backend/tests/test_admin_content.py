"""Admin content moderation of records and groups (single and bulk)."""

from sqlalchemy import select

from peerora.models import AuditLog, StudyGroup, StudyRecord
from tests.base import ApiTestCase


class AdminContentTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin_h = self.auth(self.make_user(role="admin"))
        self.owner = self.make_user(email="owner@example.com")
        owner_h = self.auth(self.owner)
        self.group = self.client.post("/api/groups", json={"name": "Physics Group"}, headers=owner_h).json()
        self.other_group = self.client.post("/api/groups", json={"name": "Chemistry Group"}, headers=owner_h).json()
        self.group_record = self.client.post(f"/api/groups/{self.group['id']}/records",
                                             json={"title": "Spam link", "status": "todo"}, headers=owner_h).json()
        self.personal = self.client.post("/api/records", json={"title": "Private notes", "status": "done"},
                                         headers=owner_h).json()

    def test_admin_sees_all_records_with_filters(self) -> None:
        def titles(query: str) -> list[str]:
            body = self.client.get(f"/api/admin/records{query}", headers=self.admin_h).json()
            return sorted(item["title"] for item in body["items"])

        self.assertEqual(titles(""), ["Private notes", "Spam link"])
        self.assertEqual(titles("?q=spam"), ["Spam link"])
        self.assertEqual(titles("?q=owner@example"), ["Private notes", "Spam link"])
        self.assertEqual(titles("?status=done"), ["Private notes"])
        self.assertEqual(titles("?scope=group"), ["Spam link"])
        self.assertEqual(titles(f"?group_id={self.group['id']}"), ["Spam link"])

    def test_admin_lists_and_searches_groups(self) -> None:
        body = self.client.get("/api/admin/groups?q=physics", headers=self.admin_h).json()
        self.assertEqual([g["name"] for g in body["items"]], ["Physics Group"])
        self.assertEqual(body["items"][0]["record_count"], 1)
        detail = self.client.get(f"/api/admin/groups/{self.group['id']}", headers=self.admin_h).json()
        self.assertEqual(len(detail["members"]), 1)

    def test_delete_single_and_bulk_records(self) -> None:
        single = self.client.delete(f"/api/admin/records/{self.group_record['id']}", headers=self.admin_h)
        self.assertEqual(single.json()["done"], 1)
        bulk = self.client.post("/api/admin/records/bulk-delete", json={"ids": [self.personal["id"], 9999]},
                                headers=self.admin_h)
        self.assertEqual(bulk.json()["done"], 1)
        self.assertEqual({r["result"] for r in bulk.json()["results"]}, {"done", "not_found"})
        with self.session_factory() as db:
            self.assertEqual(db.scalars(select(StudyRecord)).all(), [])
            deletions = db.scalars(select(AuditLog).where(AuditLog.action == "record_deleted")).all()
            self.assertEqual(len(deletions), 2)
            self.assertTrue(all(log.details["by_admin"] for log in deletions))

    def test_bulk_delete_groups(self) -> None:
        response = self.client.post("/api/admin/groups/bulk-delete",
                                    json={"ids": [self.group["id"], self.other_group["id"]]}, headers=self.admin_h)
        self.assertEqual(response.json()["done"], 2)
        with self.session_factory() as db:
            self.assertEqual(db.scalars(select(StudyGroup)).all(), [])
            # The group's records went with it (ON DELETE CASCADE).
            self.assertIsNone(db.get(StudyRecord, self.group_record["id"]))
            self.assertEqual(len(db.scalars(select(AuditLog).where(AuditLog.action == "group_deleted")).all()), 2)

    def test_admin_deleting_own_content_is_not_logged_as_moderation(self) -> None:
        own_record = self.client.post("/api/records", json={"title": "Admin notes", "status": "todo"},
                                      headers=self.admin_h).json()
        own_group = self.client.post("/api/groups", json={"name": "Admin Group"}, headers=self.admin_h).json()
        self.client.post("/api/admin/records/bulk-delete",
                         json={"ids": [own_record["id"], self.personal["id"]]}, headers=self.admin_h)
        self.client.post("/api/admin/groups/bulk-delete",
                         json={"ids": [own_group["id"], self.other_group["id"]]}, headers=self.admin_h)
        with self.session_factory() as db:
            flags = {(log.action, log.target_id): log.details["by_admin"]
                     for log in db.scalars(select(AuditLog).where(
                         AuditLog.action.in_(["record_deleted", "group_deleted"])))}
        self.assertEqual(flags, {
            ("record_deleted", str(own_record["id"])): False,
            ("record_deleted", str(self.personal["id"])): True,
            ("group_deleted", str(own_group["id"])): False,
            ("group_deleted", str(self.other_group["id"])): True,
        })

    def test_normal_user_cannot_moderate(self) -> None:
        owner_h = self.auth(self.owner)
        self.assertEqual(self.client.get("/api/admin/records", headers=owner_h).status_code, 403)
        self.assertEqual(self.client.post("/api/admin/groups/bulk-delete", json={"ids": [self.group["id"]]},
                                          headers=owner_h).status_code, 403)

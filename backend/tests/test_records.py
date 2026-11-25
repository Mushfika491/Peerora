"""Study records: personal privacy, group permissions and assignment rules."""

from sqlalchemy.exc import IntegrityError

from peerora.models import StudyRecord
from tests.test_groups import GroupTestCase


class GroupRecordTests(GroupTestCase):
    def create(self, who: str, **changes):
        body = {"title": "Normalization exercises", "status": "todo"}
        body.update(changes)
        return self.client.post(f"{self.base}/records", json=body, headers=self.h[who])

    def test_editor_and_owner_create_viewer_cannot(self) -> None:
        self.assertEqual(self.create("owner").status_code, 201)
        self.assertEqual(self.create("editor").status_code, 201)
        self.assertEqual(self.create("viewer").status_code, 403)
        self.assertEqual(self.create("outsider").status_code, 404)

    def test_all_members_can_read_group_records(self) -> None:
        self.create("editor", title="Shared task")
        for name in ("owner", "editor", "viewer"):
            with self.subTest(member=name):
                records = self.client.get(f"{self.base}/records", headers=self.h[name]).json()
                self.assertEqual([r["title"] for r in records], ["Shared task"])
        record_id = self.create("owner").json()["id"]
        self.assertEqual(self.client.get(f"/api/records/{record_id}", headers=self.h["outsider"]).status_code, 404)

    def test_assign_only_to_members(self) -> None:
        ok = self.create("editor", assigned_to_id=self.viewer.id)
        self.assertEqual(ok.status_code, 201)
        self.assertEqual(ok.json()["assigned_to_name"], "Vera Viewer")
        outsider = self.create("editor", assigned_to_id=self.outsider.id)
        self.assertEqual(outsider.status_code, 422)

    def test_viewer_cannot_edit_but_assignee_can_update_status(self) -> None:
        record = self.create("editor", assigned_to_id=self.viewer.id).json()
        url = f"/api/records/{record['id']}"
        self.assertFalse(self.client.get(url, headers=self.h["viewer"]).json()["can_edit"])
        self.assertEqual(self.client.patch(url, json={"title": "Changed"}, headers=self.h["viewer"]).status_code, 403)
        moved = self.client.patch(url, json={"status": "in_progress"}, headers=self.h["viewer"])
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["status"], "in_progress")

    def test_unassigned_viewer_cannot_change_status(self) -> None:
        record = self.create("editor").json()
        self.assertEqual(self.client.patch(f"/api/records/{record['id']}", json={"status": "done"},
                                           headers=self.h["viewer"]).status_code, 403)

    def test_editor_can_edit_and_reassign(self) -> None:
        record = self.create("owner").json()
        url = f"/api/records/{record['id']}"
        edited = self.client.patch(url, json={"title": "Edited", "assigned_to_id": self.editor.id}, headers=self.h["editor"])
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()["assigned_to_id"], self.editor.id)

    def test_delete_rules(self) -> None:
        by_owner = self.create("owner").json()["id"]
        by_editor = self.create("editor").json()["id"]
        # An editor may delete only their own records; viewers none; the owner any.
        self.assertEqual(self.client.delete(f"/api/records/{by_owner}", headers=self.h["editor"]).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/records/{by_editor}", headers=self.h["viewer"]).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/records/{by_editor}", headers=self.h["editor"]).status_code, 204)
        self.assertEqual(self.client.delete(f"/api/records/{by_owner}", headers=self.h["owner"]).status_code, 204)

    def test_removed_member_loses_assignment(self) -> None:
        record = self.create("owner", assigned_to_id=self.viewer.id).json()
        self.client.delete(f"{self.base}/members/{self.viewer.id}", headers=self.h["owner"])
        self.assertIsNone(self.client.get(f"/api/records/{record['id']}", headers=self.h["owner"]).json()["assigned_to_id"])

    def test_assigned_list_and_dashboard(self) -> None:
        self.create("editor", title="For Vera", assigned_to_id=self.viewer.id)
        assigned = self.client.get("/api/records?scope=assigned", headers=self.h["viewer"]).json()
        self.assertEqual([r["title"] for r in assigned], ["For Vera"])
        summary = self.client.get("/api/dashboard/summary", headers=self.h["viewer"]).json()
        self.assertEqual(summary["group_count"], 1)
        self.assertEqual(summary["record_counts"]["todo"], 1)
        self.assertEqual([r["title"] for r in summary["assigned_to_me"]], ["For Vera"])

    def test_deleting_group_deletes_its_records(self) -> None:
        record_id = self.create("owner").json()["id"]
        self.client.delete(self.base, headers=self.h["owner"])
        with self.session_factory() as db:
            self.assertIsNone(db.get(StudyRecord, record_id))


class PersonalRecordTests(GroupTestCase):
    def test_personal_records_are_private(self) -> None:
        created = self.client.post("/api/records", json={"title": "My notes", "content": "Private"},
                                   headers=self.h["viewer"])
        self.assertEqual(created.status_code, 201)
        record_id = created.json()["id"]
        url = f"/api/records/{record_id}"
        # Changing the id in the URL never exposes someone else's record (IDOR).
        for name in ("owner", "editor", "outsider"):
            with self.subTest(other=name):
                self.assertEqual(self.client.get(url, headers=self.h[name]).status_code, 404)
                self.assertEqual(self.client.patch(url, json={"title": "x"}, headers=self.h[name]).status_code, 404)
                self.assertEqual(self.client.delete(url, headers=self.h[name]).status_code, 404)
        mine = self.client.get("/api/records", headers=self.h["viewer"]).json()
        self.assertEqual([r["title"] for r in mine], ["My notes"])
        self.assertEqual(self.client.get("/api/records", headers=self.h["owner"]).json(), [])
        self.assertEqual(self.client.delete(url, headers=self.h["viewer"]).status_code, 204)

    def test_personal_record_cannot_be_assigned_to_someone_else(self) -> None:
        response = self.client.post("/api/records", json={"title": "Task", "assigned_to_id": self.owner.id},
                                    headers=self.h["viewer"])
        self.assertEqual(response.status_code, 422)

    def test_record_validation(self) -> None:
        for body in ({"title": ""}, {"title": "x" * 201}, {"title": "Ok", "status": "archived"},
                     {"title": "Ok", "group_id": self.group["id"]}):
            with self.subTest(body=str(body)[:40]):
                self.assertEqual(self.client.post("/api/records", json=body, headers=self.h["viewer"]).status_code, 422)

    def test_database_rejects_bad_status(self) -> None:
        with self.session_factory() as db:
            db.add(StudyRecord(title="Bad", status="archived", created_by_id=self.owner.id))
            with self.assertRaises(IntegrityError):
                db.commit()

"""Study groups: creation, membership management and the owner/editor/viewer rules."""

from sqlalchemy.exc import IntegrityError

from peerora.models import GroupMembership
from tests.base import ApiTestCase


class GroupTestCase(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.owner = self.make_user(email="owner@example.com", full_name="Olivia Owner")
        self.editor = self.make_user("tutor", email="editor@example.com", full_name="Eddie Editor")
        self.viewer = self.make_user(email="viewer@example.com", full_name="Vera Viewer")
        self.outsider = self.make_user(email="outsider@example.com", full_name="Oscar Outsider")
        self.h = {name: self.auth(user) for name, user in
                  (("owner", self.owner), ("editor", self.editor), ("viewer", self.viewer), ("outsider", self.outsider))}
        created = self.client.post("/api/groups", json={"name": "DBMS Study Group", "subject": "DBMS"},
                                   headers=self.h["owner"])
        self.assertEqual(created.status_code, 201, created.text)
        self.group = created.json()
        self.base = f"/api/groups/{self.group['id']}"
        for email, role in (("editor@example.com", "editor"), ("viewer@example.com", "viewer")):
            added = self.client.post(f"{self.base}/members", json={"email": email, "group_role": role},
                                     headers=self.h["owner"])
            self.assertEqual(added.status_code, 201, added.text)


class GroupMembershipTests(GroupTestCase):
    def test_creator_becomes_owner(self) -> None:
        self.assertEqual(self.group["my_role"], "owner")
        self.assertEqual(self.group["owner_id"], self.owner.id)
        members = self.client.get(f"{self.base}/members", headers=self.h["owner"]).json()
        self.assertEqual({m["email"]: m["group_role"] for m in members},
                         {"owner@example.com": "owner", "editor@example.com": "editor", "viewer@example.com": "viewer"})

    def test_members_see_their_groups(self) -> None:
        for name in ("owner", "editor", "viewer"):
            with self.subTest(member=name):
                groups = self.client.get("/api/groups", headers=self.h[name]).json()
                self.assertEqual([g["id"] for g in groups], [self.group["id"]])
        self.assertEqual(self.client.get("/api/groups", headers=self.h["outsider"]).json(), [])

    def test_non_members_cannot_see_anything(self) -> None:
        for path in ("", "/members", "/records"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(f"{self.base}{path}", headers=self.h["outsider"]).status_code, 404)

    def test_only_owner_can_rename_or_delete(self) -> None:
        for name in ("editor", "viewer"):
            with self.subTest(member=name):
                self.assertEqual(self.client.patch(self.base, json={"name": "Renamed"}, headers=self.h[name]).status_code, 403)
                self.assertEqual(self.client.delete(self.base, headers=self.h[name]).status_code, 403)
        self.assertEqual(self.client.patch(self.base, json={"name": "Renamed"}, headers=self.h["outsider"]).status_code, 404)
        renamed = self.client.patch(self.base, json={"name": "Renamed group"}, headers=self.h["owner"])
        self.assertEqual(renamed.json()["name"], "Renamed group")
        self.assertEqual(self.client.delete(self.base, headers=self.h["owner"]).status_code, 204)
        self.assertEqual(self.client.get(self.base, headers=self.h["editor"]).status_code, 404)

    def test_only_owner_manages_membership(self) -> None:
        add = {"email": "outsider@example.com", "group_role": "viewer"}
        self.assertEqual(self.client.post(f"{self.base}/members", json=add, headers=self.h["editor"]).status_code, 403)
        self.assertEqual(self.client.patch(f"{self.base}/members/{self.viewer.id}", json={"group_role": "editor"},
                                           headers=self.h["editor"]).status_code, 403)
        self.assertEqual(self.client.delete(f"{self.base}/members/{self.viewer.id}", headers=self.h["editor"]).status_code, 403)

        promoted = self.client.patch(f"{self.base}/members/{self.viewer.id}", json={"group_role": "editor"},
                                     headers=self.h["owner"])
        self.assertEqual(promoted.json()["group_role"], "editor")
        self.assertEqual(self.client.delete(f"{self.base}/members/{self.viewer.id}", headers=self.h["owner"]).status_code, 204)
        self.assertEqual(self.client.get(self.base, headers=self.h["viewer"]).status_code, 404)

    def test_add_member_errors(self) -> None:
        unknown = self.client.post(f"{self.base}/members", json={"email": "nobody@example.com"}, headers=self.h["owner"])
        self.assertEqual(unknown.status_code, 404)
        duplicate = self.client.post(f"{self.base}/members", json={"email": "viewer@example.com"}, headers=self.h["owner"])
        self.assertEqual(duplicate.status_code, 409)
        as_owner = self.client.post(f"{self.base}/members", json={"email": "outsider@example.com", "group_role": "owner"},
                                    headers=self.h["owner"])
        self.assertEqual(as_owner.status_code, 422)

    def test_owner_role_cannot_be_changed_and_owner_cannot_leave(self) -> None:
        self.assertEqual(self.client.patch(f"{self.base}/members/{self.owner.id}", json={"group_role": "viewer"},
                                           headers=self.h["owner"]).status_code, 403)
        self.assertEqual(self.client.delete(f"{self.base}/members/{self.owner.id}", headers=self.h["owner"]).status_code, 403)

    def test_member_can_leave(self) -> None:
        self.assertEqual(self.client.delete(f"{self.base}/members/{self.viewer.id}", headers=self.h["viewer"]).status_code, 204)
        self.assertEqual(self.client.get(self.base, headers=self.h["viewer"]).status_code, 404)

    def test_group_validation(self) -> None:
        self.assertEqual(self.client.post("/api/groups", json={"name": "A"}, headers=self.h["owner"]).status_code, 422)
        self.assertEqual(self.client.post("/api/groups", json={"name": "Ok name", "owner_id": 5},
                                          headers=self.h["owner"]).status_code, 422)

    def test_database_rejects_duplicate_membership(self) -> None:
        with self.session_factory() as db:
            db.add(GroupMembership(group_id=self.group["id"], user_id=self.viewer.id, group_role="viewer"))
            with self.assertRaises(IntegrityError):
                db.commit()

    def test_database_rejects_unknown_group_role(self) -> None:
        with self.session_factory() as db:
            db.add(GroupMembership(group_id=self.group["id"], user_id=self.outsider.id, group_role="superuser"))
            with self.assertRaises(IntegrityError):
                db.commit()

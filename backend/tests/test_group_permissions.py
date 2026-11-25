"""Independent member permissions: create, update and assign shared records.

Each test calls the API directly, so these are the same checks a member would
hit if they bypassed the UI.
"""

from sqlalchemy import select

from peerora.models import AuditLog
from tests.base import ApiTestCase

NONE = {"can_create_records": False, "can_update_records": False, "can_assign_records": False}
ALL = {"can_create_records": True, "can_update_records": True, "can_assign_records": True}


class GroupPermissionTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.owner = self.make_user(email="owner@example.com", full_name="Olivia Owner")
        self.member = self.make_user(email="member@example.com", full_name="Mia Member")
        self.other = self.make_user(email="other@example.com", full_name="Omar Other")
        self.outsider = self.make_user(email="outsider@example.com")
        self.h_owner, self.h_member = self.auth(self.owner), self.auth(self.member)
        self.h_other, self.h_outsider = self.auth(self.other), self.auth(self.outsider)
        self.group = self.client.post("/api/groups", json={"name": "Permissions Group"}, headers=self.h_owner).json()
        self.base = f"/api/groups/{self.group['id']}"
        for email in ("member@example.com", "other@example.com"):
            self.client.post(f"{self.base}/members", json={"email": email, "group_role": "viewer"}, headers=self.h_owner)
        # A record owned by the owner, assigned to "other", for edit/assign checks.
        self.record = self.client.post(f"{self.base}/records", json={"title": "Owner task", "assigned_to_id": self.other.id},
                                       headers=self.h_owner).json()
        self.record_url = f"/api/records/{self.record['id']}"

    def set_permissions(self, user_id: int, **permissions):
        return self.client.patch(f"{self.base}/members/{user_id}", json=permissions, headers=self.h_owner)

    def member_row(self, email: str) -> dict:
        members = self.client.get(f"{self.base}/members", headers=self.h_owner).json()
        return next(m for m in members if m["email"] == email)

    # ---- owner authority and labels ----

    def test_owner_holds_every_permission(self) -> None:
        self.assertEqual(self.group["my_role"], "owner")
        self.assertEqual(self.group["my_permissions"], ALL)
        self.assertEqual({k: self.member_row("owner@example.com")[k] for k in ALL}, ALL)

    def test_presets_and_derived_labels(self) -> None:
        self.assertEqual(self.member_row("member@example.com")["group_role"], "viewer")
        editor = self.set_permissions(self.member.id, group_role="editor").json()
        self.assertEqual((editor["group_role"], {k: editor[k] for k in ALL}), ("editor", ALL))
        custom = self.set_permissions(self.member.id, can_assign_records=False).json()
        self.assertEqual(custom["group_role"], "member")  # a mix of permissions
        back = self.set_permissions(self.member.id, group_role="viewer").json()
        self.assertEqual((back["group_role"], {k: back[k] for k in ALL}), ("viewer", NONE))

    def test_add_member_with_individual_permissions(self) -> None:
        added = self.client.post(f"{self.base}/members", headers=self.h_owner, json={
            "email": "outsider@example.com", "group_role": "viewer", "can_create_records": True,
        }).json()
        self.assertEqual(added["group_role"], "member")
        self.assertEqual({k: added[k] for k in ALL},
                         {"can_create_records": True, "can_update_records": False, "can_assign_records": False})

    def test_member_sees_their_own_permissions(self) -> None:
        self.set_permissions(self.member.id, can_create_records=True)
        group = self.client.get(self.base, headers=self.h_member).json()
        self.assertEqual(group["my_permissions"]["can_create_records"], True)
        self.assertEqual(group["my_permissions"]["can_assign_records"], False)

    def test_only_the_owner_can_change_permissions(self) -> None:
        self.set_permissions(self.member.id, group_role="editor")  # even a full editor cannot
        attempt = self.client.patch(f"{self.base}/members/{self.other.id}", json={"can_create_records": True},
                                    headers=self.h_member)
        self.assertEqual(attempt.status_code, 403)
        self_grant = self.client.patch(f"{self.base}/members/{self.other.id}", json={"group_role": "editor"},
                                       headers=self.h_other)
        self.assertEqual(self_grant.status_code, 403)
        outsider = self.client.patch(f"{self.base}/members/{self.member.id}", json={"group_role": "editor"},
                                     headers=self.h_outsider)
        self.assertEqual(outsider.status_code, 404)
        owner_target = self.set_permissions(self.owner.id, can_create_records=False)
        self.assertEqual(owner_target.status_code, 403)
        self.assertEqual(self.set_permissions(self.member.id).status_code, 422)  # nothing to change

    def test_permission_changes_are_audited(self) -> None:
        self.set_permissions(self.member.id, can_update_records=True)
        with self.session_factory() as db:
            log = db.scalar(select(AuditLog).where(AuditLog.action == "member_permissions_changed"))
        self.assertEqual(log.target_user_id, self.member.id)
        self.assertEqual(log.details["to"]["can_update_records"], True)
        self.assertEqual(log.details["from"]["can_update_records"], False)

    # ---- create ----

    def test_create_permission_alone(self) -> None:
        body = {"title": "Member task"}
        self.assertEqual(self.client.post(f"{self.base}/records", json=body, headers=self.h_member).status_code, 403)
        self.set_permissions(self.member.id, can_create_records=True)
        created = self.client.post(f"{self.base}/records", json=body, headers=self.h_member)
        self.assertEqual(created.status_code, 201)
        self.assertFalse(created.json()["can_edit"])
        self.assertFalse(created.json()["can_assign"])
        # Creating WITH an assignee also needs the assign permission.
        with_assignee = self.client.post(f"{self.base}/records", json={**body, "assigned_to_id": self.member.id},
                                         headers=self.h_member)
        self.assertEqual(with_assignee.status_code, 403)
        # Without update permission the member cannot edit, even their own record.
        own = f"/api/records/{created.json()['id']}"
        self.assertEqual(self.client.patch(own, json={"title": "Changed"}, headers=self.h_member).status_code, 403)

    # ---- update ----

    def test_update_permission_alone(self) -> None:
        self.assertEqual(self.client.patch(self.record_url, json={"title": "x"}, headers=self.h_member).status_code, 403)
        self.set_permissions(self.member.id, can_update_records=True)
        edited = self.client.patch(self.record_url, json={"title": "Edited", "status": "in_progress"},
                                   headers=self.h_member)
        self.assertEqual(edited.status_code, 200)
        self.assertTrue(edited.json()["can_edit"])
        # ...but not create or re-assign.
        self.assertEqual(self.client.post(f"{self.base}/records", json={"title": "n"}, headers=self.h_member).status_code, 403)
        reassign = self.client.patch(self.record_url, json={"assigned_to_id": self.member.id}, headers=self.h_member)
        self.assertEqual(reassign.status_code, 403)
        unassign = self.client.patch(self.record_url, json={"assigned_to_id": None}, headers=self.h_member)
        self.assertEqual(unassign.status_code, 403)
        # Sending the unchanged assignee (as the edit form does) is not an assignment.
        same = self.client.patch(self.record_url, json={"title": "Again", "assigned_to_id": self.other.id},
                                 headers=self.h_member)
        self.assertEqual(same.status_code, 200)

    # ---- assign ----

    def test_assign_permission_alone(self) -> None:
        self.assertEqual(self.client.patch(self.record_url, json={"assigned_to_id": self.member.id},
                                           headers=self.h_member).status_code, 403)
        self.set_permissions(self.member.id, can_assign_records=True)
        assigned = self.client.patch(self.record_url, json={"assigned_to_id": self.member.id}, headers=self.h_member)
        self.assertEqual(assigned.status_code, 200)
        self.assertTrue(assigned.json()["can_assign"])
        self.assertFalse(assigned.json()["can_edit"])
        # Assigning does not allow editing content or assigning outside the group.
        self.assertEqual(self.client.patch(self.record_url, json={"title": "x"}, headers=self.h_member).status_code, 403)
        outside = self.client.patch(self.record_url, json={"assigned_to_id": self.outsider.id}, headers=self.h_member)
        self.assertEqual(outside.status_code, 422)

    # ---- assignee status and delete rules ----

    def test_assignee_can_always_update_status_only(self) -> None:
        """'other' is a viewer (no permissions) but is the record's assignee."""
        moved = self.client.patch(self.record_url, json={"status": "done"}, headers=self.h_other)
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["status"], "done")
        self.assertEqual(self.client.patch(self.record_url, json={"title": "x"}, headers=self.h_other).status_code, 403)
        self.assertEqual(self.client.patch(self.record_url, json={"status": "todo", "title": "x"},
                                           headers=self.h_other).status_code, 403)

    def test_delete_rules(self) -> None:
        self.set_permissions(self.member.id, group_role="editor")
        mine = self.client.post(f"{self.base}/records", json={"title": "Mine"}, headers=self.h_member).json()
        # A member with update permission may delete only records they created.
        self.assertEqual(self.client.delete(self.record_url, headers=self.h_member).status_code, 403)
        self.set_permissions(self.member.id, can_update_records=False)
        self.assertEqual(self.client.delete(f"/api/records/{mine['id']}", headers=self.h_member).status_code, 403)
        self.set_permissions(self.member.id, can_update_records=True)
        self.assertEqual(self.client.delete(f"/api/records/{mine['id']}", headers=self.h_member).status_code, 204)
        # The owner may delete anything.
        self.assertEqual(self.client.delete(self.record_url, headers=self.h_owner).status_code, 204)

    def test_revoking_a_permission_takes_effect_immediately(self) -> None:
        self.set_permissions(self.member.id, group_role="editor")
        self.assertEqual(self.client.post(f"{self.base}/records", json={"title": "a"}, headers=self.h_member).status_code, 201)
        self.set_permissions(self.member.id, can_create_records=False)
        self.assertEqual(self.client.post(f"{self.base}/records", json={"title": "b"}, headers=self.h_member).status_code, 403)

    def test_outsiders_still_see_nothing(self) -> None:
        self.assertEqual(self.client.get(self.record_url, headers=self.h_outsider).status_code, 404)
        self.assertEqual(self.client.post(f"{self.base}/records", json={"title": "x"}, headers=self.h_outsider).status_code, 404)

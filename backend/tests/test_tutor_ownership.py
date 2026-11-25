"""Tutor profiles are linked to accounts and only their owner (or an admin) can change them."""

from sqlalchemy import select

from peerora.models import AuditLog, Tutor
from tests.base import ApiTestCase
from tests.test_tutors_api import valid_payload


class TutorOwnershipTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.alice = self.make_user("tutor")
        self.bob = self.make_user("tutor")
        self.student = self.make_user("student")
        self.admin = self.make_user("student", role="admin")
        self.alice_headers = self.auth(self.alice)
        response = self.client.post("/api/tutors", json=valid_payload(), headers=self.alice_headers)
        self.assertEqual(response.status_code, 201)
        self.tutor = response.json()
        self.url = f"/api/tutors/{self.tutor['id']}"

    def test_profile_is_linked_to_the_creating_account(self) -> None:
        self.assertEqual(self.tutor["user_id"], self.alice.id)
        mine = self.client.get("/api/tutors/me", headers=self.alice_headers)
        self.assertEqual(mine.json()["id"], self.tutor["id"])
        self.assertEqual(self.client.get("/api/users/me", headers=self.alice_headers).json()["has_tutor_profile"], True)

    def test_only_tutor_accounts_can_create_profiles(self) -> None:
        response = self.client.post("/api/tutors", json=valid_payload(student_id="TST0002"),
                                    headers=self.auth(self.student))
        self.assertEqual(response.status_code, 403)

    def test_one_profile_per_account(self) -> None:
        again = self.client.post("/api/tutors", json=valid_payload(student_id="TST0002"), headers=self.alice_headers)
        self.assertEqual(again.status_code, 409)
        self.assertEqual(again.json()["detail"], "You already have a tutor profile.")

    def test_another_tutor_cannot_edit_or_delete(self) -> None:
        bob_headers = self.auth(self.bob)
        self.assertEqual(self.client.put(self.url, json=valid_payload(full_name="Hacked"), headers=bob_headers).status_code, 403)
        self.assertEqual(self.client.delete(self.url, headers=bob_headers).status_code, 403)
        self.assertEqual(self.client.get(self.url).json()["full_name"], "Test Tutor")

    def test_students_can_view_but_not_change_profiles(self) -> None:
        headers = self.auth(self.student)
        view = self.client.get(self.url, headers=headers)
        self.assertEqual(view.status_code, 200)
        self.assertNotIn("student_id", view.json())  # private to owner and admins
        self.assertEqual(self.client.put(self.url, json=valid_payload(), headers=headers).status_code, 403)
        self.assertEqual(self.client.delete(self.url, headers=headers).status_code, 403)

    def test_anonymous_writes_return_401(self) -> None:
        self.assertEqual(self.client.post("/api/tutors", json=valid_payload()).status_code, 401)
        self.assertEqual(self.client.put(self.url, json=valid_payload()).status_code, 401)
        self.assertEqual(self.client.delete(self.url).status_code, 401)

    def test_admin_can_moderate_and_it_is_audited(self) -> None:
        admin_headers = self.auth(self.admin)
        view = self.client.get(self.url, headers=admin_headers)
        self.assertIn("student_id", view.json())
        edited = self.client.put(self.url, json=valid_payload(headline="Edited by moderator"), headers=admin_headers)
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(self.client.delete(self.url, headers=admin_headers).status_code, 204)
        with self.session_factory() as db:
            actions = db.scalars(select(AuditLog.action)).all()
        self.assertIn("tutor_profile_moderated", actions)
        self.assertIn("tutor_profile_deleted", actions)

    def test_legacy_profiles_without_owner_are_admin_only(self) -> None:
        with self.session_factory() as db:
            legacy = db.get(Tutor, self.tutor["id"])
            legacy.user_id = None
            db.commit()
        self.assertEqual(self.client.put(self.url, json=valid_payload(), headers=self.alice_headers).status_code, 403)
        admin_headers = self.auth(self.admin)
        linked = self.client.patch(f"/api/admin/tutors/{self.tutor['id']}/owner", json={"user_id": self.bob.id},
                                   headers=admin_headers)
        self.assertEqual(linked.status_code, 200)
        self.assertEqual(linked.json()["user_id"], self.bob.id)
        self.assertEqual(self.client.put(self.url, json=valid_payload(), headers=self.auth(self.bob)).status_code, 200)

    def test_admin_cannot_link_profile_to_a_student_account(self) -> None:
        response = self.client.patch(f"/api/admin/tutors/{self.tutor['id']}/owner",
                                     json={"user_id": self.student.id}, headers=self.auth(self.admin))
        self.assertEqual(response.status_code, 422)

    def test_tutor_profile_removed_when_owner_link_is_deleted_keeps_data(self) -> None:
        """Deleting the owner account keeps the profile (ON DELETE SET NULL)."""
        with self.session_factory() as db:
            from peerora.models import User
            db.delete(db.get(User, self.alice.id))
            db.commit()
            profile = db.scalar(select(Tutor).where(Tutor.id == self.tutor["id"]))
            self.assertIsNotNone(profile)
            self.assertIsNone(profile.user_id)

"""Tutor profile regression tests (the mid-term CRUD behaviour), adapted to
the new rules: writes need a tutor account, one profile per account, and the
Student ID is private (only the owner and administrators receive it).

Run all backend tests from the backend folder:

    python -m unittest discover -s tests -t . -v
"""

import unittest
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from main import app
from peerora.config import get_cors_origins
from peerora.models import Tutor
from tests.base import ApiTestCase

DUPLICATE_MESSAGE = "A tutor with this University Student ID already exists."
RESPONSE_KEYS = {
    "id", "user_id", "full_name", "student_id", "department", "semester", "cgpa", "headline",
    "bio", "subjects", "teaching_mode", "hourly_rate", "tutoring_experience",
    "profile_image_url", "created_at", "updated_at",
}
PUBLIC_KEYS = RESPONSE_KEYS - {"student_id"}


def valid_payload(**changes: object) -> dict[str, object]:
    """A valid request body. Pass keyword arguments to change fields."""
    payload: dict[str, object] = {
        "full_name": "Test Tutor",
        "student_id": "TST0001",
        "department": "Computer Science and Engineering",
        "semester": 5,
        "cgpa": 3.75,
        "headline": "CSE Student | Python Tutor",
        "bio": "I enjoy explaining programming concepts with small examples.",
        "subjects": ["Algorithms", "Data Structures"],
        "teaching_mode": "online",
        "hourly_rate": 500,
        "tutoring_experience": "under_6_months",
        "profile_image_url": None,
    }
    payload.update(changes)
    return payload


def messages(response) -> str:
    """All validation messages of a 422 response, joined into one text."""
    return " ".join(item["msg"] for item in response.json()["detail"])


class TutorApiTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.owner_headers: dict[int, dict[str, str]] = {}
        self.tutor_headers = self.auth(self.make_user("tutor"))

    def create(self, **changes: object):
        """Create a profile as a brand-new tutor account (one profile per account)."""
        headers = self.auth(self.make_user("tutor"))
        response = self.client.post("/api/tutors", json=valid_payload(**changes), headers=headers)
        if response.status_code == 201:
            self.owner_headers[response.json()["id"]] = headers
        return response

    # ---- Route registration ----

    def test_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]
        self.assertTrue({"get", "post"} <= set(paths["/api/tutors"]))
        self.assertTrue({"get", "put", "delete"} <= set(paths["/api/tutors/{tutor_id}"]))
        self.assertIn("/api/health", paths)
        self.assertIn("/api/tutors/me", paths)

    # ---- The five CRUD operations ----

    def test_create_returns_201_with_database_generated_fields(self) -> None:
        response = self.create()
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(set(data), RESPONSE_KEYS)
        self.assertIsInstance(data["id"], int)
        self.assertIsInstance(data["user_id"], int)
        self.assertEqual(data["student_id"], "TST0001")
        self.assertEqual(data["semester"], 5)
        self.assertEqual(data["subjects"], ["Algorithms", "Data Structures"])
        self.assertIsNone(data["profile_image_url"])
        self.assertIsInstance(data["created_at"], str)
        self.assertIsInstance(data["updated_at"], str)

    def test_numbers_are_json_numbers_not_text(self) -> None:
        response = self.create()
        data = response.json()
        self.assertIsInstance(data["cgpa"], float)
        self.assertEqual(data["cgpa"], 3.75)
        self.assertIsInstance(data["hourly_rate"], float)
        self.assertEqual(data["hourly_rate"], 500)
        self.assertNotIn('"cgpa":"', response.text)
        self.assertNotIn('"hourly_rate":"', response.text)

    def test_list_is_a_plain_public_array_newest_first(self) -> None:
        self.assertEqual(self.client.get("/api/tutors").json(), [])
        first = self.create(student_id="TST0001").json()
        second = self.create(student_id="TST0002").json()
        response = self.client.get("/api/tutors")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual([item["id"] for item in data], [second["id"], first["id"]])
        self.assertEqual(response.headers["X-Total-Count"], "2")
        # The Student ID is private and never appears in the public list.
        self.assertTrue(all(set(item) == PUBLIC_KEYS for item in data))

    def test_get_one_public_and_owner_views(self) -> None:
        created = self.create().json()
        public = self.client.get(f"/api/tutors/{created['id']}")
        self.assertEqual(public.status_code, 200)
        self.assertNotIn("student_id", public.json())

        owner = self.client.get(f"/api/tutors/{created['id']}", headers=self.owner_headers[created["id"]])
        self.assertEqual(owner.json(), created)

        missing = self.client.get("/api/tutors/99999")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json(), {"detail": "Tutor not found."})

    def test_put_replaces_all_fields(self) -> None:
        created = self.create().json()
        headers = self.owner_headers[created["id"]]
        changes = valid_payload(
            full_name="Updated Name",
            cgpa=3.5,
            hourly_rate=None,
            subjects=["Machine Learning"],
            teaching_mode="both",
            tutoring_experience="over_2_years",
            profile_image_url="https://example.com/photo.png",
        )
        response = self.client.put(f"/api/tutors/{created['id']}", json=changes, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], created["id"])
        self.assertEqual(data["full_name"], "Updated Name")
        self.assertEqual(data["cgpa"], 3.5)
        self.assertIsNone(data["hourly_rate"])
        self.assertEqual(data["subjects"], ["Machine Learning"])
        self.assertEqual(data["teaching_mode"], "both")
        self.assertEqual(data["profile_image_url"], "https://example.com/photo.png")
        self.assertEqual(self.client.get(f"/api/tutors/{created['id']}", headers=headers).json(), data)

    def test_put_missing_tutor_returns_404(self) -> None:
        response = self.client.put("/api/tutors/99999", json=valid_payload(), headers=self.tutor_headers)
        self.assertEqual(response.status_code, 404)

    def test_delete_returns_204_without_body(self) -> None:
        created = self.create().json()
        headers = self.owner_headers[created["id"]]
        response = self.client.delete(f"/api/tutors/{created['id']}", headers=headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(self.client.get(f"/api/tutors/{created['id']}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/tutors/{created['id']}", headers=headers).status_code, 404)

    # ---- Duplicate student IDs ----

    def test_duplicate_student_id_returns_409(self) -> None:
        self.assertEqual(self.create().status_code, 201)
        response = self.create(full_name="Someone Else")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": DUPLICATE_MESSAGE})
        self.assertEqual(len(self.client.get("/api/tutors").json()), 1)

    def test_update_cannot_take_another_tutors_student_id(self) -> None:
        self.create(student_id="TST0001")
        second = self.create(student_id="TST0002").json()
        url = f"/api/tutors/{second['id']}"
        headers = self.owner_headers[second["id"]]

        clash = self.client.put(url, json=valid_payload(student_id="TST0001"), headers=headers)
        self.assertEqual(clash.status_code, 409)
        self.assertEqual(clash.json(), {"detail": DUPLICATE_MESSAGE})

        same = self.client.put(url, json=valid_payload(student_id="TST0002", full_name="Renamed"), headers=headers)
        self.assertEqual(same.status_code, 200)

    def test_student_id_is_text_trimmed_and_case_sensitive(self) -> None:
        leading_zeros = self.create(student_id="0012345").json()
        self.assertEqual(leading_zeros["student_id"], "0012345")

        trimmed = self.create(student_id="  7654321  ").json()
        self.assertEqual(trimmed["student_id"], "7654321")

        self.assertEqual(self.create(student_id="abcdefg").status_code, 201)
        self.assertEqual(self.create(student_id="ABCDEFG").status_code, 201)

    # ---- Validation and invalid input ----

    def test_invalid_values_return_422_with_clear_messages(self) -> None:
        cases = [
            ("student id too short", {"student_id": "TST001"}, "University Student ID must be exactly 7"),
            ("student id too long", {"student_id": "TST00012"}, "University Student ID must be exactly 7"),
            ("name too short", {"full_name": "A"}, "Full name must be at least 2"),
            ("name too long", {"full_name": "x" * 101}, "Full name must be at most 100"),
            ("cgpa too high", {"cgpa": 4.01}, "CGPA must be between 0.00 and 4.00"),
            ("cgpa negative", {"cgpa": -0.5}, "CGPA must be between 0.00 and 4.00"),
            ("cgpa 3 decimals", {"cgpa": 3.456}, "CGPA can have at most 2 decimal places"),
            ("cgpa text", {"cgpa": "abc"}, "CGPA must be a number"),
            ("semester zero", {"semester": 0}, "Semester must be a whole number from 1 to 24"),
            ("semester 25", {"semester": 25}, "Semester must be a whole number from 1 to 24"),
            ("headline too long", {"headline": "x" * 101}, "Headline must be at most 100"),
            ("headline blank", {"headline": "   "}, "Headline is required"),
            ("about me too long", {"bio": "x" * 501}, "About Me must be at most 500"),
            ("no subjects", {"subjects": []}, "Select at least one subject"),
            ("unknown subject", {"subjects": ["Astrology"]}, "Subjects contains a subject that is not in the allowed list"),
            ("duplicate subject", {"subjects": ["Algorithms", "Algorithms"]}, "same subject more than once"),
            ("unknown department", {"department": "Astrology"}, "Department must be one of the listed departments"),
            ("old teaching mode", {"teaching_mode": "hybrid"}, "Teaching mode must be one of"),
            ("unknown experience", {"tutoring_experience": "expert"}, "Previous tutoring experience must be one of"),
            ("negative rate", {"hourly_rate": -1}, "Hourly rate cannot be negative"),
            ("rate 3 decimals", {"hourly_rate": 10.555}, "Hourly rate can have at most 2 decimal places"),
            ("rate too large", {"hourly_rate": 10000000000}, "Hourly rate is too large"),
            ("image not a web address", {"profile_image_url": "ftp://example.com/a.png"}, "must be a valid web address"),
            ("image not a url", {"profile_image_url": "not a url"}, "must be a valid web address"),
            ("unknown field", {"nickname": "Tutor"}, "is not an accepted field"),
            ("owner in body", {"user_id": 1}, "is not an accepted field"),
        ]
        for name, changes, expected in cases:
            with self.subTest(name):
                response = self.client.post("/api/tutors", json=valid_payload(**changes), headers=self.tutor_headers)
                self.assertEqual(response.status_code, 422)
                self.assertIn(expected, messages(response))
        self.assertEqual(self.client.get("/api/tutors").json(), [])

    def test_missing_required_field_returns_422(self) -> None:
        payload = valid_payload()
        del payload["full_name"]
        response = self.client.post("/api/tutors", json=payload, headers=self.tutor_headers)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Full name is required", messages(response))

    def test_malformed_and_missing_body(self) -> None:
        bad_json = self.client.post(
            "/api/tutors", content="{not json",
            headers={"Content-Type": "application/json", **self.tutor_headers},
        )
        self.assertEqual(bad_json.status_code, 422)
        self.assertIn("not valid JSON", messages(bad_json))

        no_body = self.client.post("/api/tutors", headers=self.tutor_headers)
        self.assertEqual(no_body.status_code, 422)
        self.assertIn("Request body is required", messages(no_body))

    def test_boundary_values_are_accepted(self) -> None:
        cases = [
            {"cgpa": 0, "semester": 1, "hourly_rate": 0},
            {"cgpa": 4.0, "semester": 24, "hourly_rate": None},
            {"cgpa": 2.5, "hourly_rate": 9999999999.99},
            {"headline": "h" * 100, "bio": "b" * 500, "full_name": "n" * 100},
        ]
        for index, changes in enumerate(cases, start=1):
            with self.subTest(changes=list(changes)):
                response = self.create(student_id=f"TST{index:04d}", **changes)
                self.assertEqual(response.status_code, 201, response.text)

    def test_invalid_tutor_id_in_address(self) -> None:
        for address in ("/api/tutors/abc", "/api/tutors/0"):
            with self.subTest(address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, 422)
                self.assertIn("Tutor id must be a positive whole number", messages(response))

    def test_server_side_search_and_filters(self) -> None:
        self.create(student_id="TST0001", full_name="Alice Algorithms", subjects=["Algorithms"], teaching_mode="online")
        self.create(student_id="TST0002", full_name="Bob Networks", subjects=["Computer Networks"],
                    teaching_mode="in_person", department="Economics")
        names = lambda query: [t["full_name"] for t in self.client.get(f"/api/tutors{query}").json()]  # noqa: E731
        self.assertEqual(names("?subject=Algorithms"), ["Alice Algorithms"])
        self.assertEqual(names("?teaching_mode=in_person"), ["Bob Networks"])
        self.assertEqual(names("?department=Economics"), ["Bob Networks"])
        self.assertEqual(names("?q=alice"), ["Alice Algorithms"])
        self.assertEqual(names("?q=networks"), ["Bob Networks"])  # matches a subject too
        self.assertEqual(names("?subject=Astrology"), [])
        limited = self.client.get("/api/tutors?limit=1&offset=1")
        self.assertEqual(len(limited.json()), 1)
        self.assertEqual(limited.headers["X-Total-Count"], "2")

    def test_database_constraints_reject_bad_rows_directly(self) -> None:
        """The database itself refuses invalid data, even without the Pydantic checks."""
        with self.session_factory() as session:
            session.add(
                Tutor(
                    full_name="Bad Row",
                    student_id="TST0009",
                    department="Law",
                    semester=25,  # outside 1-24
                    cgpa=Decimal("3.00"),
                    headline="Headline",
                    bio="Bio",
                    subjects=["Algorithms"],
                    teaching_mode="online",
                    hourly_rate=None,
                    tutoring_experience="none",
                    profile_image_url=None,
                )
            )
            with self.assertRaises(IntegrityError):
                session.commit()

    # ---- CORS ----

    def test_cors_allows_configured_origins_and_blocks_others(self) -> None:
        origins = get_cors_origins()
        self.assertIn("http://localhost:5173", origins)

        for origin in origins:
            with self.subTest(origin=origin):
                preflight = self.client.options(
                    "/api/tutors",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type, authorization",
                    },
                )
                self.assertEqual(preflight.status_code, 200)
                self.assertEqual(preflight.headers.get("access-control-allow-origin"), origin)
                self.assertEqual(preflight.headers.get("access-control-allow-credentials"), "true")

                actual = self.client.get("/api/tutors", headers={"Origin": origin})
                self.assertEqual(actual.headers.get("access-control-allow-origin"), origin)

        blocked = self.client.options(
            "/api/tutors",
            headers={
                "Origin": "https://not-allowed.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(blocked.status_code, 400)
        self.assertIsNone(blocked.headers.get("access-control-allow-origin"))


if __name__ == "__main__":
    unittest.main()

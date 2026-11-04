"""Live smoke test of the tutor API against the REAL database.

Run it ONLY after the migration has been approved and applied, with the backend
running (fastapi dev main.py --port 8000). It creates two test tutors whose
Student IDs start with "TST" and deletes ONLY those two (by id) at the end.
It never modifies or deletes any other record and prints no credentials.

Usage (from the backend folder):  python tests/live_smoke_test.py [base_url]
"""

import sys
import time

import httpx

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
DUPLICATE_MESSAGE = "A tutor with this University Student ID already exists."

failures: list[str] = []
created_ids: list[int] = []  # ids created by THIS run; only these are ever deleted


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    if not condition:
        failures.append(name)
        if detail:
            print(f"        {detail}")


def payload(student_id: str, **changes: object) -> dict[str, object]:
    data: dict[str, object] = {
        "full_name": "TST Smoke Test Tutor",
        "student_id": student_id,
        "department": "Computer Science and Engineering",
        "semester": 6,
        "cgpa": 3.25,
        "headline": "TST smoke test record",
        "bio": "Temporary record created by the smoke test. It is deleted at the end.",
        "subjects": ["Algorithms", "Operating Systems"],
        "teaching_mode": "both",
        "hourly_rate": 450.5,
        "tutoring_experience": "1_to_2_years",
        "profile_image_url": None,
    }
    data.update(changes)
    return data


def run(client: httpx.Client) -> None:
    seed = int(time.time()) % 8000 + 1000  # four digits, so the id is "TST" + 4 digits
    first_sid, second_sid = f"TST{seed}", f"TST{seed + 1}"

    check("health endpoint answers 200", client.get("/api/health").status_code == 200)

    before = client.get("/api/tutors")
    check("list answers 200 with a plain array", before.status_code == 200 and isinstance(before.json(), list))
    before_count = len(before.json())

    created = client.post("/api/tutors", json=payload(first_sid))
    if created.status_code != 201:
        check("create answers 201", False, f"status {created.status_code}: {created.text[:200]}")
        print("Stopping: nothing was created, so nothing will be deleted.")
        return
    first = created.json()
    created_ids.append(first["id"])
    check("create answers 201", True)
    check("created tutor has an integer id", isinstance(first["id"], int))
    check("cgpa and hourly rate are JSON numbers", isinstance(first["cgpa"], float) and isinstance(first["hourly_rate"], float))
    check("subjects come back as a list", first["subjects"] == ["Algorithms", "Operating Systems"])

    second = client.post("/api/tutors", json=payload(second_sid))
    if second.status_code == 201:
        created_ids.append(second.json()["id"])
    check("second create answers 201", second.status_code == 201)

    duplicate = client.post("/api/tutors", json=payload(first_sid))
    check("duplicate Student ID answers 409", duplicate.status_code == 409 and duplicate.json() == {"detail": DUPLICATE_MESSAGE})

    invalid = client.post("/api/tutors", json=payload("TST0000", cgpa=4.5))
    check("invalid CGPA answers 422", invalid.status_code == 422)

    one = client.get(f"/api/tutors/{first['id']}")
    check("get one answers 200 and matches", one.status_code == 200 and one.json() == first)

    listing = client.get("/api/tutors")
    listed_ids = {item["id"] for item in listing.json()} if listing.status_code == 200 else set()
    check("list contains the created tutors", set(created_ids) <= listed_ids)

    updated = client.put(f"/api/tutors/{first['id']}", json=payload(first_sid, full_name="TST Updated", hourly_rate=None))
    check("put answers 200 and replaces fields", updated.status_code == 200 and updated.json()["full_name"] == "TST Updated" and updated.json()["hourly_rate"] is None)

    if len(created_ids) == 2:
        clash = client.put(f"/api/tutors/{first['id']}", json=payload(second_sid))
        check("put with another tutor's Student ID answers 409", clash.status_code == 409)

    check("missing tutor answers 404", client.get("/api/tutors/2147483647").status_code == 404)

    deleted = client.delete(f"/api/tutors/{first['id']}")
    check("delete answers 204 with no body", deleted.status_code == 204 and deleted.content == b"")
    check("deleted tutor answers 404", client.get(f"/api/tutors/{first['id']}").status_code == 404)


def main() -> int:
    print(f"Smoke test against {BASE_URL}")
    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        try:
            run(client)
        finally:
            # Cleanup: delete only the records created by this run, by id.
            for tutor_id in created_ids:
                response = client.delete(f"/api/tutors/{tutor_id}")
                print(f"cleanup: tutor {tutor_id} -> {response.status_code} (204 = deleted, 404 = already gone)")
    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED:", "; ".join(failures))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
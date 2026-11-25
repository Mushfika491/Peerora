"""Live smoke test against a RUNNING deployment (local or production).

It creates no data. It checks public endpoints, that protected and admin
routes are refused without the right token, and (if credentials are given)
the full login -> refresh -> logout cycle with a NON-admin demo account.

Credentials come only from environment variables and are never printed:
    SMOKE_EMAIL, SMOKE_PASSWORD   (a normal Student or Tutor demo account)

Usage (from the backend folder):
    python tests/live_smoke_test.py http://localhost:8000
    SMOKE_EMAIL=... SMOKE_PASSWORD=... python tests/live_smoke_test.py https://<deployment>
"""

import os
import sys

import httpx

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
CSRF = {"X-Requested-With": "peerora"}
failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    if not condition:
        failures.append(name)
        if detail:
            print(f"        {detail}")


def run(client: httpx.Client) -> None:
    check("health endpoint answers 200", client.get("/api/health").json() == {"status": "ok"})
    check("API documentation at /api/docs", client.get("/api/docs").status_code == 200)

    tutors = client.get("/api/tutors?limit=5")
    check("public tutor list answers 200 with an array", tutors.status_code == 200 and isinstance(tutors.json(), list))
    check("public tutor list hides Student IDs",
          all("student_id" not in item for item in tutors.json()) if tutors.status_code == 200 else False)
    check("tutor list sends X-Total-Count", "x-total-count" in tutors.headers)

    check("protected route without token answers 401", client.get("/api/users/me").status_code == 401)
    check("admin route without token answers 401", client.get("/api/admin/overview").status_code == 401)
    check("forged token answers 401",
          client.get("/api/users/me", headers={"Authorization": "Bearer forged.token.value"}).status_code == 401)

    email, password = os.environ.get("SMOKE_EMAIL"), os.environ.get("SMOKE_PASSWORD")
    if not email or not password:
        print("SMOKE_EMAIL/SMOKE_PASSWORD not set: skipping the login cycle.")
        return

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    check("login answers 200", login.status_code == 200, f"status {login.status_code}")
    if login.status_code != 200:
        return
    set_cookie = login.headers.get("set-cookie", "")
    check("refresh cookie is HttpOnly", "HttpOnly" in set_cookie)
    if BASE_URL.startswith("https://"):
        check("refresh cookie is Secure on HTTPS", "Secure" in set_cookie)
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = client.get("/api/users/me", headers=headers)
    check("/api/users/me works with the access token", me.status_code == 200)
    check("demo account is a normal user", me.json().get("role") == "user")
    check("normal user gets 403 on admin routes",
          client.get("/api/admin/overview", headers=headers).status_code == 403)

    refreshed = client.post("/api/auth/refresh", headers=CSRF)
    check("refresh rotates the session (200)", refreshed.status_code == 200)
    check("logout answers 204", client.post("/api/auth/logout", headers=CSRF).status_code == 204)
    check("refresh after logout answers 401", client.post("/api/auth/refresh", headers=CSRF).status_code == 401)


def main() -> int:
    print(f"Smoke test against {BASE_URL}")
    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        run(client)
    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED:", "; ".join(failures))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

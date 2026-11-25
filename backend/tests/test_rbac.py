"""RBAC: every protected route rejects anonymous callers (401), every admin
route rejects normal users (403), and the permission map is central."""

import re

from main import app
from peerora.core.permissions import ROLE_PERMISSIONS, Permission, has_permission
from tests.base import ApiTestCase

# Routes that anyone may call without a token.
PUBLIC_ROUTES = {
    ("GET", "/api/health"),
    ("GET", "/api/tutors"),
    ("GET", "/api/tutors/{tutor_id}"),
    ("POST", "/api/auth/signup"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/logout"),
    ("GET", "/api/auth/password-reset/availability"),
    ("POST", "/api/auth/password-reset/request"),
    ("POST", "/api/auth/password-reset/confirm"),
}


def all_api_routes() -> list[tuple[str, str]]:
    routes = []
    for path, methods in app.openapi()["paths"].items():
        for method in methods:
            routes.append((method.upper(), path))
    return routes


def concrete(path: str) -> str:
    """Fill every {placeholder} with a valid-looking id."""
    return re.sub(r"\{[^}]+\}", "1", path)


class PermissionMapTests(ApiTestCase):
    def test_admins_hold_every_permission_users_hold_only_their_own(self) -> None:
        self.assertEqual(ROLE_PERMISSIONS["admin"], frozenset(Permission))
        self.assertTrue(has_permission("user", Permission.GROUP_CREATE))
        for permission in (Permission.ADMIN_ACCESS, Permission.USER_BAN, Permission.ROLE_CHANGE,
                           Permission.CONTENT_MODERATE, Permission.AUDIT_READ, Permission.DATA_EXPORT):
            self.assertFalse(has_permission("user", permission))
        self.assertFalse(has_permission("unknown-role", Permission.GROUP_CREATE))


class ProtectedRouteTests(ApiTestCase):
    def test_every_protected_route_requires_a_token(self) -> None:
        checked = 0
        for method, path in all_api_routes():
            if (method, path) in PUBLIC_ROUTES:
                continue
            with self.subTest(route=f"{method} {path}"):
                response = self.client.request(method, concrete(path), json={})
                self.assertEqual(response.status_code, 401, response.text)
                checked += 1
        self.assertGreater(checked, 30)

    def test_every_admin_route_is_forbidden_for_normal_users(self) -> None:
        headers = self.auth(self.make_user("tutor"))
        admin_routes = [(m, p) for m, p in all_api_routes() if p.startswith("/api/admin")]
        self.assertGreater(len(admin_routes), 15)
        for method, path in admin_routes:
            with self.subTest(route=f"{method} {path}"):
                response = self.client.request(method, concrete(path), json={}, headers=headers)
                self.assertEqual(response.status_code, 403, response.text)

    def test_admin_can_reach_admin_routes(self) -> None:
        headers = self.auth(self.make_user(role="admin"))
        for path in ("/api/admin/overview", "/api/admin/users", "/api/admin/records",
                     "/api/admin/groups", "/api/admin/audit-logs", "/api/admin/security/failed-logins"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=headers).status_code, 200)

    def test_user_only_endpoints_work_for_users(self) -> None:
        headers = self.auth(self.make_user())
        for path in ("/api/users/me", "/api/users/me/sessions", "/api/groups", "/api/records",
                     "/api/dashboard/summary"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=headers).status_code, 200)


class ErrorShapeTests(ApiTestCase):
    def test_unexpected_errors_return_a_generic_500(self) -> None:
        from fastapi.testclient import TestClient

        @app.get("/api/__test_crash__", include_in_schema=False)
        def crash():
            raise RuntimeError("secret internal detail")

        try:
            client = TestClient(app, raise_server_exceptions=False)
            # The error is logged on the server (captured here), never sent to the client.
            with self.assertLogs("peerora", level="ERROR") as logs:
                response = client.get("/api/__test_crash__")
            self.assertIn("Unhandled error", logs.output[0])
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"detail": "An unexpected error occurred. Please try again later."})
            self.assertNotIn("secret internal detail", response.text)
            self.assertNotIn("Traceback", response.text)
        finally:
            app.router.routes = [r for r in app.router.routes if getattr(r, "path", "") != "/api/__test_crash__"]

    def test_security_headers_are_sent(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["cache-control"], "no-store")
        csp = response.headers["content-security-policy"]
        self.assertIn("default-src 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        # Error responses carry it too.
        self.assertIn("default-src 'none'", self.client.get("/api/users/me").headers["content-security-policy"])

    def test_docs_pages_are_not_blocked_by_the_api_csp(self) -> None:
        """Swagger UI loads scripts from a CDN, so the strict API policy must not apply."""
        for path in ("/api/docs", "/api/redoc"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("content-security-policy", response.headers)

    def test_api_documentation_is_available(self) -> None:
        self.assertEqual(self.client.get("/api/docs").status_code, 200)
        self.assertEqual(self.client.get("/api/openapi.json").status_code, 200)

"""Timestamps are stored in UTC and always returned with an explicit UTC offset;
the stored user agent identifies Brave when the browser says so."""

import csv
import io
import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from peerora.core.request_info import USER_AGENT_MAX_LENGTH, brand_from_client_hints, describe_user_agent
from peerora.models import AuditLog
from peerora.models.helpers import UtcDateTime
from tests.base import PASSWORD, ApiTestCase

CHROME_LINUX = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36")
FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0"
BRAVE_HINTS = '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
CHROME_HINTS = '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
EDGE_HINTS = '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
DHAKA = timezone(timedelta(hours=6))


def parse_api_time(value: str) -> datetime:
    """What a browser does: parse ISO 8601. It must carry a timezone."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None, f"timestamp without timezone: {value}"
    return parsed


class UtcColumnTypeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.column = UtcDateTime()

    def test_values_are_converted_to_utc_before_storage(self) -> None:
        dhaka_noon = datetime(2026, 11, 24, 12, 0, tzinfo=DHAKA)
        self.assertEqual(self.column.process_bind_param(dhaka_noon, None),
                         datetime(2026, 11, 24, 6, 0, tzinfo=timezone.utc))
        naive = datetime(2026, 11, 24, 6, 0)  # naive values are UTC by convention
        self.assertEqual(self.column.process_bind_param(naive, None).tzinfo, timezone.utc)
        self.assertIsNone(self.column.process_bind_param(None, None))

    def test_values_are_read_back_as_aware_utc(self) -> None:
        from_sqlite = datetime(2026, 11, 24, 0, 37)  # SQLite returns naive values
        self.assertEqual(self.column.process_result_value(from_sqlite, None),
                         datetime(2026, 11, 24, 0, 37, tzinfo=timezone.utc))
        from_postgres = datetime(2026, 11, 24, 6, 37, tzinfo=DHAKA)  # session timezone
        self.assertEqual(self.column.process_result_value(from_postgres, None),
                         datetime(2026, 11, 24, 0, 37, tzinfo=timezone.utc))


class TimestampApiTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_user(role="admin", email="admin@example.com")
        self.h = self.auth(self.admin)

    def add_log(self, action: str, when: datetime) -> None:
        with self.session_factory() as db:
            db.add(AuditLog(action=action, created_at=when))
            db.commit()

    def test_storage_stays_utc(self) -> None:
        self.add_log("probe", datetime(2026, 11, 24, 6, 37, tzinfo=DHAKA))  # = 00:37 UTC
        with self.session_factory() as db:
            raw = db.execute(text("SELECT created_at FROM audit_logs WHERE action = 'probe'")).scalar()
        self.assertTrue(str(raw).startswith("2026-11-24 00:37"))

    def test_api_timestamps_carry_a_utc_offset(self) -> None:
        self.login("admin@example.com")
        logs = self.client.get("/api/admin/audit-logs", headers=self.h).json()["items"]
        created = parse_api_time(logs[0]["created_at"])
        self.assertEqual(created.utcoffset(), timedelta(0))
        self.assertLess(abs((datetime.now(timezone.utc) - created).total_seconds()), 60)
        # Other endpoints use the same column type.
        me = self.client.get("/api/users/me", headers=self.h).json()
        parse_api_time(me["created_at"])
        for session in self.client.get("/api/users/me/sessions", headers=self.h).json():
            for field in ("created_at", "last_used_at", "expires_at"):
                parse_api_time(session[field])
        for user in self.client.get("/api/admin/users", headers=self.h).json()["items"]:
            parse_api_time(user["created_at"])

    def test_date_filters_respect_timezone_offsets(self) -> None:
        """A Bangladesh admin asking for "24 Nov from midnight" sends 2026-11-24T00:00+06:00
        (= 23 Nov 18:00 UTC). Events are compared in UTC, whatever offset is sent."""
        self.add_log("before_window", datetime(2026, 11, 23, 17, 30, tzinfo=timezone.utc))  # 23:30 Dhaka, 23 Nov
        self.add_log("inside_window", datetime(2026, 11, 23, 18, 30, tzinfo=timezone.utc))  # 00:30 Dhaka, 24 Nov
        self.add_log("later_inside", datetime(2026, 11, 24, 10, 0, tzinfo=timezone.utc))

        def actions(query: str) -> list[str]:
            items = self.client.get(f"/api/admin/audit-logs{query}", headers=self.h).json()["items"]
            return [i["action"] for i in items if i["action"] not in ("login_success",)]

        local_midnight = "2026-11-24T00:00:00%2B06:00"  # "+" must be URL-encoded
        self.assertEqual(actions(f"?date_from={local_midnight}"), ["later_inside", "inside_window"])
        self.assertEqual(actions("?date_from=2026-11-23T18:00:00Z"), ["later_inside", "inside_window"])
        self.assertEqual(actions(f"?date_to={local_midnight}"), ["before_window"])

    def test_sorting_is_by_true_time(self) -> None:
        self.add_log("older", datetime(2026, 11, 24, 6, 0, tzinfo=DHAKA))   # 00:00 UTC
        self.add_log("newer", datetime(2026, 11, 24, 0, 30, tzinfo=timezone.utc))
        items = self.client.get("/api/admin/audit-logs?q=er", headers=self.h).json()["items"]
        names = [i["action"] for i in items if i["action"] in ("older", "newer")]
        self.assertEqual(names, ["newer", "older"])

    def test_csv_export_times_are_explicit_utc(self) -> None:
        self.add_log("exported", datetime(2026, 11, 24, 6, 37, tzinfo=DHAKA))
        rows = list(csv.DictReader(io.StringIO(
            self.client.get("/api/admin/exports/audit-logs.csv?action=exported", headers=self.h).text)))
        self.assertEqual(rows[0]["created_at_utc"], "2026-11-24T00:37:00+00:00")
        users = list(csv.DictReader(io.StringIO(
            self.client.get("/api/admin/exports/users.csv", headers=self.h).text)))
        self.assertTrue(users[0]["created_at_utc"].endswith("+00:00"))


class BrowserIdentificationTests(unittest.TestCase):
    def test_brave_is_found_in_client_hints(self) -> None:
        self.assertEqual(brand_from_client_hints(BRAVE_HINTS), ("Brave", "131"))
        self.assertIsNone(brand_from_client_hints(CHROME_HINTS))
        self.assertIsNone(brand_from_client_hints(EDGE_HINTS))
        self.assertIsNone(brand_from_client_hints(None))
        self.assertIsNone(brand_from_client_hints("garbage"))

    def test_brave_token_is_added_only_for_brave(self) -> None:
        self.assertTrue(describe_user_agent(CHROME_LINUX, BRAVE_HINTS, None).endswith(" Brave/131"))
        self.assertEqual(describe_user_agent(CHROME_LINUX, CHROME_HINTS, None), CHROME_LINUX)
        self.assertEqual(describe_user_agent(CHROME_LINUX, EDGE_HINTS, None), CHROME_LINUX)
        self.assertEqual(describe_user_agent(CHROME_LINUX, None, None), CHROME_LINUX)  # unidentifiable: stays Chrome
        self.assertEqual(describe_user_agent(FIREFOX_LINUX, None, None), FIREFOX_LINUX)

    def test_frontend_hint_is_a_fallback_and_strictly_validated(self) -> None:
        self.assertTrue(describe_user_agent(CHROME_LINUX, None, "Brave").endswith(" Brave"))
        self.assertEqual(describe_user_agent(CHROME_LINUX, None, "Vivaldi"), CHROME_LINUX)
        self.assertEqual(describe_user_agent(CHROME_LINUX, None, "<script>alert(1)</script>"), CHROME_LINUX)
        # The client hint (with version) wins over the frontend hint.
        self.assertTrue(describe_user_agent(CHROME_LINUX, BRAVE_HINTS, "Brave").endswith(" Brave/131"))

    def test_no_duplicate_token_and_length_limit_kept(self) -> None:
        already = CHROME_LINUX + " Brave/131"
        self.assertEqual(describe_user_agent(already, BRAVE_HINTS, None), already)
        long_agent = CHROME_LINUX + " X" * 200
        stored = describe_user_agent(long_agent, BRAVE_HINTS, None)
        self.assertLessEqual(len(stored), USER_AGENT_MAX_LENGTH)
        self.assertTrue(stored.endswith(" Brave/131"))
        self.assertIsNone(describe_user_agent(None, BRAVE_HINTS, None))


class BrowserInAuditLogTests(ApiTestCase):
    def logged_agent(self, headers: dict[str, str]) -> str:
        self.client.post("/api/auth/login", json={"email": "sam@example.com", "password": PASSWORD}, headers=headers)
        with self.session_factory() as db:
            return db.scalars(select(AuditLog.user_agent).order_by(AuditLog.id.desc())).first()

    def test_login_from_brave_is_logged_as_brave(self) -> None:
        self.make_user(email="sam@example.com")
        agent = self.logged_agent({"User-Agent": CHROME_LINUX, "Sec-CH-UA": BRAVE_HINTS})
        self.assertTrue(agent.endswith("Brave/131"))
        agent = self.logged_agent({"User-Agent": CHROME_LINUX, "X-Client-Brand": "Brave"})
        self.assertTrue(agent.endswith(" Brave"))

    def test_login_from_chrome_and_firefox_is_unchanged(self) -> None:
        self.make_user(email="sam@example.com")
        self.assertEqual(self.logged_agent({"User-Agent": CHROME_LINUX, "Sec-CH-UA": CHROME_HINTS}), CHROME_LINUX)
        self.assertEqual(self.logged_agent({"User-Agent": FIREFOX_LINUX}), FIREFOX_LINUX)

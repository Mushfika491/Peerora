"""Configuration and database-engine behaviour (secrets are fake test values).

Every test patches os.environ, so the developer's real backend/.env values are
never read, printed or changed, and the local dev database is never opened.
"""

import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sqlalchemy import text

from peerora import config, database




class DatabaseUrlTests(unittest.TestCase):
    def tearDown(self) -> None:
        mock.patch.stopall()

    def test_postgres_urls_select_psycopg3(self) -> None:
        for given in ("postgres://u:p@h:5432/db", "postgresql://u:p@h:5432/db"):
            with self.subTest(given=given.split(":")[0]):
                with mock.patch.dict(os.environ, {"DATABASE_URL": given}):
                    self.assertEqual(config.get_database_url(), "postgresql+psycopg://u:p@h:5432/db")

    def test_sqlite_url_is_kept(self) -> None:
        with mock.patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./x.db"}):
            self.assertEqual(config.get_database_url(), "sqlite:///./x.db")

    def test_missing_url_raises_without_leaking_values(self) -> None:
        with mock.patch.dict(os.environ, {"DATABASE_URL": "   "}):
            with self.assertRaises(RuntimeError) as caught:
                config.get_database_url()
        self.assertIn("DATABASE_URL is not set", str(caught.exception))


class SecretAndSettingTests(unittest.TestCase):
    def test_secrets_must_be_long_enough_and_errors_never_echo_them(self) -> None:
        short = "short-secret-value"
        for name, getter in (("JWT_SECRET_KEY", config.get_jwt_secret), ("PASSWORD_PEPPER", config.get_password_pepper)):
            with self.subTest(name=name), mock.patch.dict(os.environ, {name: short[:10]}):
                with self.assertRaises(RuntimeError) as caught:
                    getter()
                self.assertIn(name, str(caught.exception))
                self.assertNotIn(short[:10], str(caught.exception))

    def test_access_token_lifetime_is_capped_at_15_minutes(self) -> None:
        for value, expected in (("60", 15), ("5", 5), ("0", 1), ("not-a-number", 15)):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"ACCESS_TOKEN_MINUTES": value}):
                self.assertEqual(config.get_access_token_minutes(), expected)

    def test_refresh_days_have_a_floor(self) -> None:
        with mock.patch.dict(os.environ, {"REFRESH_TOKEN_DAYS": "-3"}):
            self.assertEqual(config.get_refresh_token_days(), 1)

    def test_app_refuses_to_start_without_valid_secrets_and_never_shows_them(self) -> None:
        from fastapi.testclient import TestClient

        from main import app

        short = "tooShort9"
        for name in ("JWT_SECRET_KEY", "PASSWORD_PEPPER"):
            records: list[logging.LogRecord] = []
            handler = logging.Handler()
            handler.emit = records.append
            logging.getLogger().addHandler(handler)
            try:
                with self.subTest(name=name), mock.patch.dict(os.environ, {name: short}):
                    with self.assertRaises(RuntimeError) as caught:
                        with TestClient(app):  # "with" runs the startup (lifespan) code
                            pass
                    self.assertIn(name, str(caught.exception))
                    self.assertNotIn(short, str(caught.exception))
                    self.assertFalse(any(short in record.getMessage() for record in records))
            finally:
                logging.getLogger().removeHandler(handler)

    def test_app_starts_with_valid_secrets(self) -> None:
        from fastapi.testclient import TestClient

        from main import app

        valid = {"JWT_SECRET_KEY": "k" * 32, "PASSWORD_PEPPER": "p" * 16}
        with mock.patch.dict(os.environ, valid), TestClient(app) as client:
            self.assertEqual(client.get("/api/health").json(), {"status": "ok"})

    def test_cookie_secure_defaults_to_true(self) -> None:
        with mock.patch.dict(os.environ, {"COOKIE_SECURE": ""}):
            self.assertTrue(config.cookie_secure())
        for value, expected in (("false", False), ("0", False), ("TRUE", True), ("yes", True)):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"COOKIE_SECURE": value}):
                self.assertEqual(config.cookie_secure(), expected)

    def test_proxy_headers_trusted_on_vercel_or_when_enabled(self) -> None:
        with mock.patch.dict(os.environ, {"TRUST_PROXY_HEADERS": "", "VERCEL": "1"}):
            self.assertTrue(config.trust_proxy_headers())
        with mock.patch.dict(os.environ, {"TRUST_PROXY_HEADERS": "", "VERCEL": ""}):
            self.assertFalse(config.trust_proxy_headers())
        with mock.patch.dict(os.environ, {"TRUST_PROXY_HEADERS": "false", "VERCEL": "1"}):
            self.assertFalse(config.trust_proxy_headers())

    def test_cors_origins(self) -> None:
        with mock.patch.dict(os.environ, {"CORS_ORIGINS": " https://a.example/ , http://localhost:5173 "}):
            self.assertEqual(config.get_cors_origins(), ["https://a.example", "http://localhost:5173"])
        with mock.patch.dict(os.environ, {"CORS_ORIGINS": ""}):
            self.assertEqual(config.get_cors_origins(), ["http://localhost:5173"])
        with mock.patch.dict(os.environ, {"CORS_ORIGINS": "*"}):
            with self.assertRaises(ValueError):
                config.get_cors_origins()


class EngineTests(unittest.TestCase):
    """get_engine() for local SQLite development (production uses PostgreSQL)."""

    def setUp(self) -> None:
        database.get_engine.cache_clear()
        database.get_session_factory.cache_clear()
        self.folder = tempfile.TemporaryDirectory()
        self.db_path = Path(self.folder.name) / "engine-test.db"
        self.env = mock.patch.dict(os.environ, {"DATABASE_URL": f"sqlite:///{self.db_path}"})
        self.env.start()

    def tearDown(self) -> None:
        engine = database.get_engine()
        engine.dispose()
        database.get_engine.cache_clear()
        database.get_session_factory.cache_clear()
        self.env.stop()
        self.folder.cleanup()

    def test_sqlite_engine_enforces_foreign_keys(self) -> None:
        engine = database.get_engine()
        self.assertEqual(engine.dialect.name, "sqlite")
        with engine.connect() as connection:
            self.assertEqual(connection.execute(text("PRAGMA foreign_keys")).scalar(), 1)
        self.assertEqual(str(engine.url.database), str(self.db_path))  # never the dev database

    def test_get_db_yields_a_working_session_and_closes_it(self) -> None:
        generator = database.get_db()
        session = next(generator)
        self.assertEqual(session.execute(text("SELECT 1")).scalar(), 1)
        with self.assertRaises(StopIteration):
            next(generator)


class PostgresEngineSettingsTests(unittest.TestCase):
    def test_postgres_engine_uses_a_small_pooler_safe_pool(self) -> None:
        database.get_engine.cache_clear()
        try:
            with mock.patch.dict(os.environ, {"DATABASE_URL": "postgresql://u:p@127.0.0.1:1/db"}):
                engine = database.get_engine()  # creating an engine does not connect
                self.assertEqual(engine.dialect.name, "postgresql")
                self.assertEqual(engine.dialect.driver, "psycopg")
                self.assertEqual(engine.pool.size(), 3)
                engine.dispose()
        finally:
            database.get_engine.cache_clear()

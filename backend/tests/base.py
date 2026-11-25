"""Shared test setup: the real FastAPI app on a fresh in-memory SQLite
database per test. Supabase is never touched.

Test-only secrets are set here, before the app is imported.
"""

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-key-0123456789abcdef")
os.environ.setdefault("PASSWORD_PEPPER", "test-only-pepper-0123456789")
os.environ.setdefault("COOKIE_SECURE", "false")

import itertools  # noqa: E402
import unittest  # noqa: E402
import warnings  # noqa: E402
from functools import lru_cache  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.exc import SAWarning  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from main import app  # noqa: E402
from peerora.config import CSRF_HEADER_NAME, CSRF_HEADER_VALUE  # noqa: E402
from peerora.core.request_info import ClientInfo  # noqa: E402
from peerora.core.security import create_access_token, hash_password  # noqa: E402
from peerora.database import Base, get_db  # noqa: E402
from peerora.models import User  # noqa: E402
from peerora.services import session_service  # noqa: E402

# SQLite stores decimals as floats and SQLAlchemy warns about it. That is fine in tests.
warnings.filterwarnings("ignore", category=SAWarning)

PASSWORD = "Password123"
CSRF = {CSRF_HEADER_NAME: CSRF_HEADER_VALUE}
_emails = itertools.count(1)


@lru_cache
def password_hash() -> str:
    """Argon2 is deliberately slow, so the test password is hashed once."""
    return hash_password(PASSWORD)


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        # SQLite only enforces foreign keys (and ON DELETE CASCADE) when asked.
        @event.listens_for(self.engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record) -> None:
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

        def override_get_db():
            session = self.session_factory()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    # ---- helpers ----

    def new_client(self) -> TestClient:
        """A second browser with its own cookie jar."""
        return TestClient(app)

    def make_user(
        self, account_type: str = "student", role: str = "user", email: str | None = None,
        full_name: str = "Test User", banned: bool = False,
    ) -> User:
        with self.session_factory() as db:
            user = User(
                email=email or f"user{next(_emails)}@example.com",
                full_name=full_name,
                password_hash=password_hash(),
                account_type=account_type,
                role=role,
                is_banned=banned,
                ban_reason="Test ban" if banned else None,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    def auth(self, user: User) -> dict[str, str]:
        """Authorization header for a fresh session of this user (no HTTP login needed)."""
        with self.session_factory() as db:
            session, _ = session_service.start_session(db, db.get(User, user.id), ClientInfo("127.0.0.1", "tests"))
            db.commit()
            token = create_access_token(user.id, user.role, session.id)
        return {"Authorization": f"Bearer {token}"}

    def login(self, email: str, password: str = PASSWORD, client: TestClient | None = None):
        return (client or self.client).post("/api/auth/login", json={"email": email, "password": password})

    def bearer(self, response) -> dict[str, str]:
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def db_get(self, model, ident):
        with self.session_factory() as db:
            return db.get(model, ident)

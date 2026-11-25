"""Local development only: create a throwaway SQLite database with demo data.

It refuses to run unless DATABASE_URL points at SQLite, so it can never touch
Supabase. The schema comes from the models and is then stamped at the newest
Alembic revision, so future migrations apply to it normally. The demo password
is read from DEV_DEMO_PASSWORD.

Usage (from the backend folder):
    DEV_DEMO_PASSWORD=... python -m scripts.dev_setup
"""

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from peerora import models  # noqa: F401  (registers every table)
from peerora.config import get_database_url
from peerora.database import Base, get_engine, get_session_factory
from peerora.schemas.common import check_password_strength
from scripts.seed_demo import ACCOUNTS, seed


def main() -> int:
    if not get_database_url().startswith("sqlite"):
        print("Refusing to run: DATABASE_URL is not a local SQLite database.")
        return 1
    password = os.environ.get("DEV_DEMO_PASSWORD", "")
    try:
        check_password_strength(password)
    except ValueError as error:
        print(f"DEV_DEMO_PASSWORD {error}.")
        return 1
    Base.metadata.create_all(get_engine())
    # Record that this schema equals the newest migration, so later migrations
    # can be applied to this local database with `alembic upgrade head`.
    command.stamp(Config(str(Path(__file__).resolve().parent.parent / "alembic.ini")), "head")
    with get_session_factory()() as db:
        seed(db, {key: password for key, *_ in ACCOUNTS})
        db.commit()
    print("Local development database is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

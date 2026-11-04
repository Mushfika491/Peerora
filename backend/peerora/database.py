"""Database connection: the SQLAlchemy engine, sessions, and the model base class."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from peerora.config import get_database_url


class Base(DeclarativeBase):
    """Parent class of every table model (the Tutor model is added in a later step)."""


@lru_cache
def get_engine() -> Engine:
    """Create the engine once. The engine manages a small pool of connections."""
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,  # test a connection before using it, so stale ones are replaced
        pool_size=3,  # the Supabase pooler limits connections, so keep the pool small
        max_overflow=2,
        # Turns off Psycopg 3's prepared statements. This makes the same code work
        # with both Supabase pooler modes (session and transaction).
        connect_args={"prepare_threshold": None},
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create the factory that builds database sessions."""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: give each request its own session and always close it."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
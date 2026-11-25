"""Small helpers shared by the model files."""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


def in_list(column: str, values: tuple[str, ...]) -> str:
    """Build SQL such as: role IN ('user', 'admin')."""
    quoted = ", ".join("'" + value.replace("'", "''") + "'" for value in values)
    return f"{column} IN ({quoted})"


class UtcDateTime(TypeDecorator):
    """A timestamp that is always stored as UTC and always read back as a
    timezone-aware UTC datetime.

    PostgreSQL (timestamptz) keeps the timezone, but SQLite (local development
    and tests) does not: without this, SQLite returns "naive" datetimes, the
    API sends them without an offset, and browsers then misread UTC as local
    time. The database columns are unchanged (TIMESTAMP WITH TIME ZONE), so no
    migration is needed.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)  # naive values are UTC by convention
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)  # SQLite: stored as UTC, returned naive
        return value.astimezone(timezone.utc)

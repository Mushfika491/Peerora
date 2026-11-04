"""The tutors table, described as a Python class (a SQLAlchemy model).

Every column matches the frontend contract (frontend/src/types/tutor.ts) and
the limits in constants.py. The Alembic migration creates the same table.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from peerora.constants import (
    BIO_MAX_LENGTH,
    CGPA_MAX,
    CGPA_MIN,
    DEPARTMENTS,
    FULL_NAME_MAX_LENGTH,
    FULL_NAME_MIN_LENGTH,
    HEADLINE_MAX_LENGTH,
    PROFILE_IMAGE_URL_MAX_LENGTH,
    SEMESTER_MAX,
    SEMESTER_MIN,
    STUDENT_ID_LENGTH,
    TEACHING_MODES,
    TUTORING_EXPERIENCES,
)
from peerora.database import Base


def _in_list(column: str, values: tuple[str, ...]) -> str:
    """Build SQL such as: teaching_mode IN ('online', 'in_person', 'both')."""
    quoted = ", ".join("'" + value.replace("'", "''") + "'" for value in values)
    return f"{column} IN ({quoted})"


class Tutor(Base):
    __tablename__ = "tutors"

    # Database-level rules. They protect the data even if a request bypasses the
    # Pydantic validation. The same rules appear in the Alembic migration.
    # (The migration also checks that "subjects" is a non-empty JSON array; that
    # check uses PostgreSQL-only functions, so it lives in the migration only.)
    __table_args__ = (
        UniqueConstraint("student_id", name="uq_tutors_student_id"),
        CheckConstraint(
            f"length(full_name) >= {FULL_NAME_MIN_LENGTH} "
            f"AND length(full_name) <= {FULL_NAME_MAX_LENGTH}",
            name="ck_tutors_full_name_length",
        ),
        CheckConstraint(
            f"length(student_id) = {STUDENT_ID_LENGTH}",
            name="ck_tutors_student_id_length",
        ),
        CheckConstraint(
            _in_list("department", DEPARTMENTS), name="ck_tutors_department_allowed"
        ),
        CheckConstraint(
            f"semester >= {SEMESTER_MIN} AND semester <= {SEMESTER_MAX}",
            name="ck_tutors_semester_range",
        ),
        CheckConstraint(
            f"cgpa >= {CGPA_MIN} AND cgpa <= {CGPA_MAX}", name="ck_tutors_cgpa_range"
        ),
        CheckConstraint(
            f"length(headline) >= 1 AND length(headline) <= {HEADLINE_MAX_LENGTH}",
            name="ck_tutors_headline_length",
        ),
        CheckConstraint(
            f"length(bio) >= 1 AND length(bio) <= {BIO_MAX_LENGTH}",
            name="ck_tutors_bio_length",
        ),
        CheckConstraint(
            _in_list("teaching_mode", TEACHING_MODES),
            name="ck_tutors_teaching_mode_allowed",
        ),
        CheckConstraint(
            _in_list("tutoring_experience", TUTORING_EXPERIENCES),
            name="ck_tutors_experience_allowed",
        ),
        CheckConstraint(
            "hourly_rate IS NULL OR hourly_rate >= 0",
            name="ck_tutors_hourly_rate_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(FULL_NAME_MAX_LENGTH))
    # Text, not a number, so leading zeros are kept. Unique and case-sensitive.
    student_id: Mapped[str] = mapped_column(String(STUDENT_ID_LENGTH))
    department: Mapped[str] = mapped_column(String(100))
    semester: Mapped[int]
    cgpa: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    headline: Mapped[str] = mapped_column(String(HEADLINE_MAX_LENGTH))
    bio: Mapped[str] = mapped_column(String(BIO_MAX_LENGTH))  # shown as "About Me"
    # JSONB in PostgreSQL; plain JSON elsewhere (the tests use SQLite).
    subjects: Mapped[list[str]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    teaching_mode: Mapped[str] = mapped_column(String(20))
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    tutoring_experience: Mapped[str] = mapped_column(String(20))
    profile_image_url: Mapped[str | None] = mapped_column(
        String(PROFILE_IMAGE_URL_MAX_LENGTH)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
"""Create the tutors table.

Revision ID: 3f8a1c2d9b7e
Revises:
Create Date: 2026-11-02

The lists below are written out in full on purpose: a migration is a snapshot of
what the database looked like at this step, so it must not change when
constants.py changes later. A future change to a list needs a NEW migration.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3f8a1c2d9b7e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tutors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("student_id", sa.String(length=7), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("cgpa", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("headline", sa.String(length=100), nullable=False),
        sa.Column("bio", sa.String(length=500), nullable=False),
        sa.Column("subjects", postgresql.JSONB(), nullable=False),
        sa.Column("teaching_mode", sa.String(length=20), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("tutoring_experience", sa.String(length=20), nullable=False),
        sa.Column("profile_image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("student_id", name="uq_tutors_student_id"),
        sa.CheckConstraint(
            "length(full_name) >= 2 AND length(full_name) <= 100",
            name="ck_tutors_full_name_length",
        ),
        sa.CheckConstraint(
            "length(student_id) = 7", name="ck_tutors_student_id_length"
        ),
        sa.CheckConstraint(
            "department IN ("
            "'Accounting', "
            "'Computer Science and Engineering', "
            "'Economics', "
            "'Electrical and Electronic Engineering', "
            "'English and Modern Languages', "
            "'Environmental Science and Management', "
            "'Finance', "
            "'General Management', "
            "'Global Studies and Governance', "
            "'Human Resource Management', "
            "'International Business', "
            "'Law', "
            "'Life Sciences', "
            "'Management Information Systems', "
            "'Marketing', "
            "'Media and Communication', "
            "'Pharmacy', "
            "'Physical Sciences', "
            "'Public Health', "
            "'Social Sciences and Humanities')",
            name="ck_tutors_department_allowed",
        ),
        sa.CheckConstraint(
            "semester >= 1 AND semester <= 24", name="ck_tutors_semester_range"
        ),
        sa.CheckConstraint("cgpa >= 0 AND cgpa <= 4", name="ck_tutors_cgpa_range"),
        sa.CheckConstraint(
            "length(headline) >= 1 AND length(headline) <= 100",
            name="ck_tutors_headline_length",
        ),
        sa.CheckConstraint(
            "length(bio) >= 1 AND length(bio) <= 500", name="ck_tutors_bio_length"
        ),
        sa.CheckConstraint(
            "teaching_mode IN ('online', 'in_person', 'both')",
            name="ck_tutors_teaching_mode_allowed",
        ),
        sa.CheckConstraint(
            "tutoring_experience IN ('none', 'under_6_months', '6_to_12_months', "
            "'1_to_2_years', 'over_2_years')",
            name="ck_tutors_experience_allowed",
        ),
        sa.CheckConstraint(
            "hourly_rate IS NULL OR hourly_rate >= 0",
            name="ck_tutors_hourly_rate_nonnegative",
        ),
    )

    # PostgreSQL-only check: subjects must be a JSON array with at least one item.
    op.create_check_constraint(
        "ck_tutors_subjects_nonempty_array",
        "tutors",
        "jsonb_typeof(subjects) = 'array' AND jsonb_array_length(subjects) >= 1",
    )

    # Supabase exposes tables in the "public" schema through a public web API.
    # Row Level Security with no policies blocks that route completely. The
    # FastAPI backend connects as the table owner, which is not restricted.
    op.execute("ALTER TABLE tutors ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("tutors")
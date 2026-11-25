"""Study groups, group memberships and study records.

Revision ID: 0005_study_groups_and_records
Revises: 0004_sessions_and_security
Create Date: 2026-11-23

Additive only: three new tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_study_groups_and_records"
down_revision: Union[str, Sequence[str], None] = "0004_sessions_and_security"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "study_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name="fk_study_groups_owner_id_users", ondelete="CASCADE"),
        sa.CheckConstraint("length(name) >= 2", name="ck_study_groups_name_length"),
    )
    op.create_index("ix_study_groups_owner_id", "study_groups", ["owner_id"])
    op.create_index("ix_study_groups_name", "study_groups", ["name"])

    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_role", sa.String(length=10), nullable=False),
        sa.Column("added_by_id", sa.Integer(), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_memberships_group_id_user_id"),
        sa.ForeignKeyConstraint(
            ["group_id"], ["study_groups.id"], name="fk_group_memberships_group_id_study_groups", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_group_memberships_user_id_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["added_by_id"], ["users.id"], name="fk_group_memberships_added_by_id_users", ondelete="SET NULL"
        ),
        sa.CheckConstraint("group_role IN ('owner', 'editor', 'viewer')", name="ck_group_memberships_role_allowed"),
    )
    op.create_index("ix_group_memberships_user_id", "group_memberships", ["user_id"])

    op.create_table(
        "study_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.String(length=2000), nullable=True),
        sa.Column("status", sa.String(length=15), server_default="todo", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="fk_study_records_created_by_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["study_groups.id"], name="fk_study_records_group_id_study_groups", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_id"], ["users.id"], name="fk_study_records_assigned_to_id_users", ondelete="SET NULL"
        ),
        sa.CheckConstraint("length(title) >= 1", name="ck_study_records_title_length"),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'done')", name="ck_study_records_status_allowed"),
    )
    op.create_index("ix_study_records_group_id", "study_records", ["group_id"])
    op.create_index("ix_study_records_created_by_id", "study_records", ["created_by_id"])
    op.create_index("ix_study_records_assigned_to_id", "study_records", ["assigned_to_id"])
    op.create_index("ix_study_records_status", "study_records", ["status"])

    for table in ("study_groups", "group_memberships", "study_records"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("study_records")
    op.drop_table("group_memberships")
    op.drop_table("study_groups")

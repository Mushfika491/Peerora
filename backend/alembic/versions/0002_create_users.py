"""Create the users table (accounts, account type, security role, ban status).

Revision ID: 0002_create_users
Revises: 3f8a1c2d9b7e
Create Date: 2026-11-23

Additive only: no existing table is touched.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_users"
down_revision: Union[str, Sequence[str], None] = "3f8a1c2d9b7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("account_type", sa.String(length=10), nullable=False),
        sa.Column("role", sa.String(length=10), server_default="user", nullable=False),
        sa.Column("is_banned", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("ban_reason", sa.String(length=500), nullable=True),
        sa.Column("banned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("banned_by_id", sa.Integer(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.ForeignKeyConstraint(["banned_by_id"], ["users.id"], name="fk_users_banned_by_id_users", ondelete="SET NULL"),
        sa.CheckConstraint("account_type IN ('student', 'tutor')", name="ck_users_account_type_allowed"),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_role_allowed"),
        sa.CheckConstraint("NOT is_banned OR ban_reason IS NOT NULL", name="ck_users_ban_has_reason"),
    )
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_banned", "users", ["is_banned"])
    op.create_index("ix_users_created_at", "users", ["created_at"])
    # Same protection as the tutors table: block Supabase's public data API.
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_is_banned", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")

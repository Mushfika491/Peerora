"""Password-reset tokens (hashed, time-limited, single-use).

Revision ID: 0007_password_reset_tokens
Revises: 0006_group_member_permissions
Create Date: 2026-11-24

Additive only: one new table.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_password_reset_tokens"
down_revision: Union[str, Sequence[str], None] = "0006_group_member_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_ip", sa.String(length=45), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_password_reset_tokens_user_id_users", ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id_created_at", "password_reset_tokens", ["user_id", "created_at"]
    )
    if op.get_bind().dialect.name == "postgresql":
        # Same protection as every other table: block Supabase's public data API.
        op.execute("ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("password_reset_tokens")

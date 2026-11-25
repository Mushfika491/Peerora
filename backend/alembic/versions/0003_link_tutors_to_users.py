"""Link tutor profiles to user accounts.

Revision ID: 0003_link_tutors_to_users
Revises: 0002_create_users
Create Date: 2026-11-23

Adds a NULLABLE tutors.user_id column. Existing tutor rows keep every value
and simply get user_id = NULL (they become admin-managed until an admin links
them to a tutor account). No row is changed, deleted or rewritten.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_link_tutors_to_users"
down_revision: Union[str, Sequence[str], None] = "0002_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tutors", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tutors_user_id_users", "tutors", "users", ["user_id"], ["id"], ondelete="SET NULL"
    )
    # One profile per user. NULLs are allowed many times, so legacy rows are fine.
    op.create_unique_constraint("uq_tutors_user_id", "tutors", ["user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_tutors_user_id", "tutors", type_="unique")
    op.drop_constraint("fk_tutors_user_id_users", "tutors", type_="foreignkey")
    op.drop_column("tutors", "user_id")

"""Independent group member permissions (create / update / assign records).

Revision ID: 0006_group_member_permissions
Revises: 0005_study_groups_and_records
Create Date: 2026-11-24

Adds three boolean columns to group_memberships and allows the derived role
label "member" (a custom mix of permissions).

Existing data keeps exactly the same meaning:
  owner and editor rows -> all three permissions true
  viewer rows           -> all three permissions false
No row is deleted. Batch mode is used so the same migration also works on the
SQLite database used for local development.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_group_member_permissions"
down_revision: Union[str, Sequence[str], None] = "0005_study_groups_and_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS = ("can_create_records", "can_update_records", "can_assign_records")
OLD_ROLES_CHECK = "group_role IN ('owner', 'editor', 'viewer')"
NEW_ROLES_CHECK = "group_role IN ('owner', 'editor', 'viewer', 'member')"
CHECK_NAME = "ck_group_memberships_role_allowed"


def upgrade() -> None:
    with op.batch_alter_table("group_memberships") as batch:
        for column in PERMISSIONS:
            batch.add_column(sa.Column(column, sa.Boolean(), server_default=sa.false(), nullable=False))
        batch.drop_constraint(CHECK_NAME, type_="check")
        batch.create_check_constraint(CHECK_NAME, NEW_ROLES_CHECK)

    # Backfill: owners and editors could create, edit and assign before.
    op.execute(
        "UPDATE group_memberships SET can_create_records = TRUE, can_update_records = TRUE, "
        "can_assign_records = TRUE WHERE group_role IN ('owner', 'editor')"
    )


def downgrade() -> None:
    # Fold custom "member" rows back into the old roles before the check returns.
    op.execute(
        "UPDATE group_memberships SET group_role = 'editor' WHERE group_role = 'member' "
        "AND (can_create_records OR can_update_records OR can_assign_records)"
    )
    op.execute("UPDATE group_memberships SET group_role = 'viewer' WHERE group_role = 'member'")
    with op.batch_alter_table("group_memberships") as batch:
        batch.drop_constraint(CHECK_NAME, type_="check")
        batch.create_check_constraint(CHECK_NAME, OLD_ROLES_CHECK)
        for column in reversed(PERMISSIONS):
            batch.drop_column(column)

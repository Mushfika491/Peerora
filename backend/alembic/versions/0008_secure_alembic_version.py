"""Secure the alembic_version table from Supabase's public data API.

Revision ID: 0008_secure_alembic_version
Revises: 0007_password_reset_tokens
Create Date: 2026-11-24

Supabase exposes every table in the "public" schema through its data API, and
its default privileges give the API roles (anon, authenticated) full access.
alembic_version was the one table without Row Level Security, so anyone with
the public anon key could read or change the migration version.

This migration:
* enables RLS on alembic_version with no policies (deny-all for API roles),
* revokes every table privilege from anon and authenticated.

Alembic itself is unaffected: it connects as the table owner (postgres), and
table owners are not restricted by RLS unless FORCE ROW LEVEL SECURITY is set,
which this migration deliberately does not do.

PostgreSQL only. On SQLite (local development) it does nothing. The role
statements are skipped on PostgreSQL servers without the Supabase roles.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0008_secure_alembic_version"
down_revision: Union[str, Sequence[str], None] = "0007_password_reset_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

API_ROLES = ("anon", "authenticated")


def _for_each_api_role(statement: str) -> None:
    """Run a GRANT/REVOKE for each Supabase API role that exists on this server."""
    for role in API_ROLES:
        op.execute(
            "DO $$ BEGIN "
            f"IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN "
            f"{statement.format(role=role)}; "
            "END IF; END $$"
        )


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY")
    _for_each_api_role("REVOKE ALL ON TABLE public.alembic_version FROM {role}")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    # Restores the previous state: Supabase's default full grants and no RLS.
    _for_each_api_role("GRANT ALL ON TABLE public.alembic_version TO {role}")
    op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY")

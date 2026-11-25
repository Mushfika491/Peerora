"""Central permission model (RBAC).

Routes never compare role strings themselves. They ask for a Permission via
`require_permission(...)` (see dependencies.py), and this file is the single
place that says which security role holds which permission.
"""

from enum import StrEnum

from peerora.constants import ROLE_ADMIN, ROLE_USER


class Permission(StrEnum):
    # Every signed-in, non-banned user
    PROFILE_MANAGE_OWN = "profile:manage_own"
    TUTOR_PROFILE_MANAGE_OWN = "tutor_profile:manage_own"
    GROUP_CREATE = "group:create"
    RECORD_MANAGE_OWN = "record:manage_own"

    # Administrators only
    ADMIN_ACCESS = "admin:access"
    USER_MANAGE = "user:manage"
    USER_BAN = "user:ban"
    ROLE_CHANGE = "role:change"
    SESSION_REVOKE_ANY = "session:revoke_any"
    CONTENT_MODERATE = "content:moderate"
    AUDIT_READ = "audit:read"
    DATA_EXPORT = "data:export"


_USER_PERMISSIONS = frozenset(
    {
        Permission.PROFILE_MANAGE_OWN,
        Permission.TUTOR_PROFILE_MANAGE_OWN,
        Permission.GROUP_CREATE,
        Permission.RECORD_MANAGE_OWN,
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    ROLE_USER: _USER_PERMISSIONS,
    ROLE_ADMIN: frozenset(Permission),  # admins hold every permission
}


def has_permission(role: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())

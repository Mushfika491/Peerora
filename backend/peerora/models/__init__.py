"""All table models. Importing this package registers every table with
Base.metadata (Alembic and the tests rely on that).

`from peerora.models import Tutor` keeps working as before.
"""

from peerora.models.audit import AuditLog, LoginAttempt
from peerora.models.group import GroupMembership, StudyGroup
from peerora.models.password_reset import PasswordResetToken
from peerora.models.record import StudyRecord
from peerora.models.session import RefreshToken, UserSession
from peerora.models.tutor import Tutor
from peerora.models.user import User

__all__ = [
    "AuditLog",
    "GroupMembership",
    "LoginAttempt",
    "PasswordResetToken",
    "RefreshToken",
    "StudyGroup",
    "StudyRecord",
    "Tutor",
    "User",
    "UserSession",
]

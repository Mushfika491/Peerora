"""Create an administrator account, or promote an existing account to admin.

This is the ONLY way (besides an existing admin promoting someone in the admin
dashboard) to obtain the admin role: public signup always creates role "user".

The password is typed in at a hidden prompt. It is never read from the command
line or a file, and it is never printed or logged.

Usage (from the backend folder, with DATABASE_URL, PASSWORD_PEPPER set):
    python -m scripts.create_admin --email admin@example.com --name "Ada Admin" --account-type student
    python -m scripts.create_admin --email existing@example.com --promote
"""

import argparse
import getpass
import sys

from sqlalchemy import select

from peerora.constants import ACCOUNT_TYPES, ROLE_ADMIN
from peerora.core.security import hash_password
from peerora.database import get_session_factory
from peerora.models import User
from peerora.schemas.common import check_password_strength, normalize_email
from peerora.services.audit_service import AuditAction, log_event


def ask_password() -> str:
    while True:
        password = getpass.getpass("New admin password (hidden): ")
        try:
            check_password_strength(password)
        except ValueError as error:
            print(f"Password {error}. Try again.")
            continue
        if getpass.getpass("Repeat the password: ") != password:
            print("The passwords do not match. Try again.")
            continue
        return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or promote a Peerora administrator.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", help="Full name (for a new account)")
    parser.add_argument("--account-type", choices=ACCOUNT_TYPES, default="student")
    parser.add_argument("--promote", action="store_true", help="Promote an existing account instead")
    args = parser.parse_args()
    email = normalize_email(args.email)

    with get_session_factory()() as db:
        user = db.scalar(select(User).where(User.email == email))
        if args.promote:
            if user is None:
                print("No account with that email exists.")
                return 1
            old_role = user.role
            user.role = ROLE_ADMIN
            log_event(db, AuditAction.ROLE_CHANGED, target_user_id=user.id, target_type="user", target_id=user.id,
                      details={"from": old_role, "to": ROLE_ADMIN, "via": "create_admin script"})
            db.commit()
            print(f"User #{user.id} is now an administrator.")
            return 0

        if user is not None:
            print("An account with that email already exists. Use --promote instead.")
            return 1
        if not args.name or len(args.name.strip()) < 2:
            print("--name is required for a new account (at least 2 characters).")
            return 1
        user = User(
            email=email,
            full_name=args.name.strip(),
            password_hash=hash_password(ask_password()),
            account_type=args.account_type,
            role=ROLE_ADMIN,
        )
        db.add(user)
        db.flush()
        log_event(db, AuditAction.ROLE_CHANGED, target_user_id=user.id, target_type="user", target_id=user.id,
                  details={"to": ROLE_ADMIN, "via": "create_admin script", "created": True})
        db.commit()
        print(f"Administrator created: user #{user.id} ({user.account_type}).")
        return 0


if __name__ == "__main__":
    sys.exit(main())

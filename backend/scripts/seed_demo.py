"""Create the demonstration data required by the assessment (idempotent).

  - 2 administrators (one Student-type, one Tutor-type)
  - 4 normal users (2 students, 2 tutors), tutors with linked tutor profiles
  - personal and shared study records
  - 1 shared study group with mixed permissions (owner, editor, viewer)

Passwords: you are asked for ONE demo password per account at hidden prompts
(or one shared password if you press Enter at the per-account prompts). They
are never printed, logged, written to disk or committed. Hand them in through
the submission form only.

Running it twice changes nothing: existing accounts/groups are reused.

Usage (from the backend folder, with DATABASE_URL and PASSWORD_PEPPER set):
    python -m scripts.seed_demo            # asks before writing anything
"""

import getpass
import sys
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from peerora.constants import GROUP_ROLE_PRESETS
from peerora.core.security import hash_password
from peerora.database import get_session_factory
from peerora.models import GroupMembership, StudyGroup, StudyRecord, Tutor, User
from peerora.schemas.common import check_password_strength

ACCOUNTS = [
    # (key, email, full name, account type, role)
    ("admin1", "admin1@peerora.demo", "Ayesha Admin", "student", "admin"),
    ("admin2", "admin2@peerora.demo", "Rafiq Admin", "tutor", "admin"),
    ("student1", "student1@peerora.demo", "Nadia Student", "student", "user"),
    ("student2", "student2@peerora.demo", "Imran Student", "student", "user"),
    ("tutor1", "tutor1@peerora.demo", "Farhan Tutor", "tutor", "user"),
    ("tutor2", "tutor2@peerora.demo", "Sadia Tutor", "tutor", "user"),
]

TUTOR_PROFILES = {
    "tutor1": dict(student_id="DEMO001", department="Computer Science and Engineering", semester=8,
                   cgpa=Decimal("3.82"), headline="CSE Senior | Algorithms & Data Structures Tutor",
                   bio="I help students master algorithms through worked examples and practice problems.",
                   subjects=["Algorithms", "Data Structures", "Discrete Mathematics"], teaching_mode="both",
                   hourly_rate=Decimal("600"), tutoring_experience="1_to_2_years"),
    "tutor2": dict(student_id="DEMO002", department="Computer Science and Engineering", semester=6,
                   cgpa=Decimal("3.65"), headline="Databases and Software Engineering Tutor",
                   bio="I explain SQL, normalization and software design with real project examples.",
                   subjects=["Database Management Systems", "Software Engineering"], teaching_mode="online",
                   hourly_rate=None, tutoring_experience="6_to_12_months"),
}


def ask_passwords() -> dict[str, str]:
    shared = ""
    while not shared:
        candidate = getpass.getpass("Default demo password for all accounts (hidden): ")
        try:
            check_password_strength(candidate)
            shared = candidate
        except ValueError as error:
            print(f"Password {error}.")
    passwords = {}
    for key, email, *_ in ACCOUNTS:
        own = getpass.getpass(f"Password for {email} (Enter = default): ")
        if own:
            try:
                check_password_strength(own)
            except ValueError as error:
                print(f"Password {error}; using the default for {email}.")
                own = ""
        passwords[key] = own or shared
    return passwords


def get_or_create_user(db: Session, email, name, account_type, role, password) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, full_name=name, password_hash=hash_password(password),
                    account_type=account_type, role=role)
        db.add(user)
        db.flush()
        print(f"  created user #{user.id}: {email} ({account_type}, {role})")
    else:
        print(f"  exists: user #{user.id}: {email}")
    return user


def seed(db: Session, passwords: dict[str, str]) -> None:
    users = {key: get_or_create_user(db, email, name, kind, role, passwords[key])
             for key, email, name, kind, role in ACCOUNTS}

    for key, profile in TUTOR_PROFILES.items():
        if db.scalar(select(Tutor).where(Tutor.user_id == users[key].id)) is None:
            db.add(Tutor(full_name=users[key].full_name, user_id=users[key].id, profile_image_url=None, **profile))
            print(f"  created tutor profile for {users[key].email}")

    group = db.scalar(select(StudyGroup).where(StudyGroup.name == "CSE309 Project Group",
                                               StudyGroup.owner_id == users["student1"].id))
    if group is None:
        group = StudyGroup(name="CSE309 Project Group", subject="Software Engineering",
                           description="Shared demo group: owner, editor and viewer have different permissions.",
                           owner_id=users["student1"].id)
        db.add(group)
        db.flush()
        # Owner has every permission; editor = create + update + assign; viewer = none.
        permissions = {"owner": (True, True, True), **GROUP_ROLE_PRESETS}
        for key, role in (("student1", "owner"), ("tutor1", "editor"), ("student2", "viewer")):
            create, update, assign = permissions[role]
            db.add(GroupMembership(group_id=group.id, user_id=users[key].id, group_role=role,
                                   can_create_records=create, can_update_records=update,
                                   can_assign_records=assign, added_by_id=users["student1"].id))
        today = date.today()
        db.add_all([
            StudyRecord(group_id=group.id, created_by_id=users["student1"].id, title="Write the PRD section",
                        content="Summarise goals and user stories.", status="done", assigned_to_id=users["student1"].id),
            StudyRecord(group_id=group.id, created_by_id=users["tutor1"].id, title="Review ER diagram",
                        status="in_progress", assigned_to_id=users["tutor1"].id, due_date=today + timedelta(days=2)),
            StudyRecord(group_id=group.id, created_by_id=users["tutor1"].id, title="Prepare demo checklist",
                        status="todo", assigned_to_id=users["student2"].id, due_date=today + timedelta(days=4)),
        ])
        print(f"  created group #{group.id} with owner/editor/viewer and 3 shared records")

    for key, title in (("student1", "Revise normalization (1NF-3NF)"), ("student2", "Practice sorting algorithms")):
        exists = db.scalar(select(StudyRecord).where(StudyRecord.created_by_id == users[key].id,
                                                     StudyRecord.group_id.is_(None), StudyRecord.title == title))
        if exists is None:
            db.add(StudyRecord(created_by_id=users[key].id, title=title, status="todo"))
            print(f"  created personal record for {users[key].email}")


def main() -> int:
    print("This writes demo accounts and data to the database in DATABASE_URL.")
    if input("Type 'seed' to continue: ").strip() != "seed":
        print("Cancelled. Nothing was written.")
        return 1
    passwords = ask_passwords()
    with get_session_factory()() as db:
        seed(db, passwords)
        db.commit()
    print("Done. Demo passwords were not stored anywhere except as hashes in the database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

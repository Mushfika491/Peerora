"""Allowed values and field limits for tutor profiles.

Keep these in sync with the frontend:
- lists:  frontend/src/constants/tutorOptions.ts
- limits: frontend/src/utils/validation.ts
"""

DEPARTMENTS: tuple[str, ...] = (
    "Accounting",
    "Computer Science and Engineering",
    "Economics",
    "Electrical and Electronic Engineering",
    "English and Modern Languages",
    "Environmental Science and Management",
    "Finance",
    "General Management",
    "Global Studies and Governance",
    "Human Resource Management",
    "International Business",
    "Law",
    "Life Sciences",
    "Management Information Systems",
    "Marketing",
    "Media and Communication",
    "Pharmacy",
    "Physical Sciences",
    "Public Health",
    "Social Sciences and Humanities",
)

# The groups mirror SUBJECT_GROUPS in the frontend. To add a subject, add it
# here AND in tutorOptions.ts.
SUBJECTS: tuple[str, ...] = (
    # Programming
    "Programming Fundamentals",
    "Structured Programming",
    "Object-Oriented Programming",
    # Data and Algorithms
    "Data Structures",
    "Algorithms",
    "Database Management Systems",
    "Discrete Mathematics",
    # Systems and Hardware
    "Digital Logic Design",
    "Computer Architecture",
    "Operating Systems",
    "Computer Networks",
    # Software and Graphics
    "Software Engineering",
    "Computer Graphics",
    # Artificial Intelligence
    "Artificial Intelligence",
    "Machine Learning",
    # Theory and Compilers
    "Theory of Computation",
    "Compiler Design",
)

TEACHING_MODES: tuple[str, ...] = ("online", "in_person", "both")

TUTORING_EXPERIENCES: tuple[str, ...] = (
    "none",
    "under_6_months",
    "6_to_12_months",
    "1_to_2_years",
    "over_2_years",
)

# ---- Field limits (characters are counted the way Python's len() counts them) ----
FULL_NAME_MIN_LENGTH = 2
FULL_NAME_MAX_LENGTH = 100
STUDENT_ID_LENGTH = 7
HEADLINE_MAX_LENGTH = 100
BIO_MAX_LENGTH = 500
PROFILE_IMAGE_URL_MAX_LENGTH = 500
SEMESTER_MIN = 1
SEMESTER_MAX = 24
CGPA_MIN = 0
CGPA_MAX = 4

# ---- Accounts, roles and permissions-related values ----
# Account type = which application experience a person gets (dashboard, tutor
# profile). Security role = what the backend authorizes. They are separate on
# purpose: an admin can still be a student or a tutor.
ACCOUNT_TYPE_STUDENT = "student"
ACCOUNT_TYPE_TUTOR = "tutor"
ACCOUNT_TYPES: tuple[str, ...] = (ACCOUNT_TYPE_STUDENT, ACCOUNT_TYPE_TUTOR)

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLES: tuple[str, ...] = (ROLE_USER, ROLE_ADMIN)

USER_FULL_NAME_MIN_LENGTH = 2
USER_FULL_NAME_MAX_LENGTH = 100
EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
BAN_REASON_MAX_LENGTH = 500

# ---- Study groups and study records ----
# Each non-owner member has three independent permissions (see
# services/group_service.py). The group_role is a label derived from them:
#   editor = all three, viewer = none, member = any other combination.
# The owner always has every permission and is the only one who can rename or
# delete the group and manage members.
GROUP_ROLE_OWNER = "owner"
GROUP_ROLE_EDITOR = "editor"
GROUP_ROLE_VIEWER = "viewer"
GROUP_ROLE_MEMBER = "member"
GROUP_ROLES: tuple[str, ...] = (GROUP_ROLE_OWNER, GROUP_ROLE_EDITOR, GROUP_ROLE_VIEWER, GROUP_ROLE_MEMBER)

# The three member permissions, as (create, update, assign) presets.
GROUP_PERMISSION_FIELDS: tuple[str, ...] = ("can_create_records", "can_update_records", "can_assign_records")
GROUP_ROLE_PRESETS: dict[str, tuple[bool, bool, bool]] = {
    GROUP_ROLE_EDITOR: (True, True, True),
    GROUP_ROLE_VIEWER: (False, False, False),
}

GROUP_NAME_MIN_LENGTH = 2
GROUP_NAME_MAX_LENGTH = 100
GROUP_DESCRIPTION_MAX_LENGTH = 1000

RECORD_STATUS_TODO = "todo"
RECORD_STATUS_IN_PROGRESS = "in_progress"
RECORD_STATUS_DONE = "done"
RECORD_STATUSES: tuple[str, ...] = (RECORD_STATUS_TODO, RECORD_STATUS_IN_PROGRESS, RECORD_STATUS_DONE)
RECORD_TITLE_MAX_LENGTH = 200
RECORD_CONTENT_MAX_LENGTH = 2000

# ---- Login brute-force protection ----
# Failures are counted per (account, IP address) pair, so someone who types
# another person's email cannot lock that person out from a different network.
# A per-IP limit stops one address guessing many accounts, and a much higher
# per-account limit stops a guessing attack spread over many addresses.
LOGIN_WINDOW_MINUTES = 15
MAX_FAILED_LOGINS_PER_ACCOUNT_AND_IP = 5
MAX_FAILED_LOGINS_PER_IP = 20
MAX_FAILED_LOGINS_PER_ACCOUNT = 50

# ---- Signup rate limiting (per IP address) ----
SIGNUP_WINDOW_MINUTES = 60
MAX_SIGNUPS_PER_IP = 10

# ---- Refresh-token rotation ----
# A refresh token presented again within this many seconds of being rotated is
# treated as a concurrent request (two tabs, a network retry), not as theft.
REFRESH_REUSE_GRACE_SECONDS = 10

# ---- Password reset ----
PASSWORD_RESET_TOKEN_MINUTES = 30  # how long an emailed reset link stays valid
PASSWORD_RESET_WINDOW_MINUTES = 60
MAX_PASSWORD_RESET_REQUESTS_PER_IP = 5  # beyond this: HTTP 429
MAX_PASSWORD_RESET_EMAILS_PER_ACCOUNT = 3  # beyond this: no more emails (same generic reply)

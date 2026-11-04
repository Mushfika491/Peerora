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
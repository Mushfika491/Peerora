// ===== Departments (fixed list of 20) =====
// "as const" keeps the exact text of each item, so TypeScript can derive a
// precise Department type from this array (see types/tutor.ts).
export const DEPARTMENTS = [
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
] as const;

// ===== Semesters (1 to 24 inclusive; academic year is not used) =====
export const MIN_SEMESTER = 1;
export const MAX_SEMESTER = 24;

export const SEMESTERS: readonly number[] = Array.from(
  { length: MAX_SEMESTER - MIN_SEMESTER + 1 },
  (_, index) => MIN_SEMESTER + index
);

// ===== Teaching modes =====
// "value" is what is stored and sent to the API; "label" is what users see.
export const TEACHING_MODE_OPTIONS = [
  { value: "online", label: "Online" },
  { value: "in_person", label: "In-person" },
  { value: "both", label: "Both" },
] as const;

// ===== Previous tutoring experience =====
export const TUTORING_EXPERIENCE_OPTIONS = [
  { value: "none", label: "No formal experience — willing to teach" },
  { value: "under_6_months", label: "Less than 6 months" },
  { value: "6_to_12_months", label: "6 months–1 year" },
  { value: "1_to_2_years", label: "1–2 years" },
  { value: "over_2_years", label: "More than 2 years" },
] as const;

// ===== Subjects you can tutor (grouped) =====
// To add a subject, add its name to a group. To add a new category, add a new
// group. Nothing else in the project needs to change.
export interface SubjectGroup {
  label: string;
  subjects: readonly string[];
}

export const SUBJECT_GROUPS: readonly SubjectGroup[] = [
  {
    label: "Programming",
    subjects: [
      "Programming Fundamentals",
      "Structured Programming",
      "Object-Oriented Programming",
    ],
  },
  {
    label: "Data and Algorithms",
    subjects: [
      "Data Structures",
      "Algorithms",
      "Database Management Systems",
      "Discrete Mathematics",
    ],
  },
  {
    label: "Systems and Hardware",
    subjects: [
      "Digital Logic Design",
      "Computer Architecture",
      "Operating Systems",
      "Computer Networks",
    ],
  },
  {
    label: "Software and Graphics",
    subjects: ["Software Engineering", "Computer Graphics"],
  },
  {
    label: "Artificial Intelligence",
    subjects: ["Artificial Intelligence", "Machine Learning"],
  },
  {
    label: "Theory and Compilers",
    subjects: ["Theory of Computation", "Compiler Design"],
  },
];

// A flat list of every subject name, built automatically from the groups above.
export const ALL_SUBJECTS: readonly string[] = SUBJECT_GROUPS.flatMap(
  (group) => group.subjects
);
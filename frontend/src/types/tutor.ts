import {
  ALL_SUBJECTS,
  DEPARTMENTS,
  TEACHING_MODE_OPTIONS,
  TUTORING_EXPERIENCE_OPTIONS,
} from "../constants/tutorOptions";

// ---- Types derived from the option lists ----

// "Accounting" | "Computer Science and Engineering" | ...
export type Department = (typeof DEPARTMENTS)[number];

// "online" | "in_person" | "both"
export type TeachingMode = (typeof TEACHING_MODE_OPTIONS)[number]["value"];

// "none" | "under_6_months" | "6_to_12_months" | "1_to_2_years" | "over_2_years"
export type TutoringExperience =
  (typeof TUTORING_EXPERIENCE_OPTIONS)[number]["value"];

// ---- Runtime checks (type guards) ----
// Data from a server or a form is not trusted by TypeScript, so these
// functions verify a value at runtime and tell TypeScript its type.

const TEACHING_MODE_VALUES: readonly string[] = TEACHING_MODE_OPTIONS.map(
  (option) => option.value
);

const TUTORING_EXPERIENCE_VALUES: readonly string[] =
  TUTORING_EXPERIENCE_OPTIONS.map((option) => option.value);

export function isDepartment(value: unknown): value is Department {
  return (
    typeof value === "string" && (DEPARTMENTS as readonly string[]).includes(value)
  );
}

export function isTeachingMode(value: unknown): value is TeachingMode {
  return typeof value === "string" && TEACHING_MODE_VALUES.includes(value);
}

export function isTutoringExperience(
  value: unknown
): value is TutoringExperience {
  return typeof value === "string" && TUTORING_EXPERIENCE_VALUES.includes(value);
}

// True when the text is one of the subjects in the allowed list.
export function isKnownSubject(value: unknown): value is string {
  return typeof value === "string" && ALL_SUBJECTS.includes(value);
}

// ---- Data model ----

// The id may be a number (database integer) or a string (for example a UUID).
export type TutorId = number | string;

// The complete tutor object, exactly as returned by the backend.
export interface Tutor {
  id: TutorId;
  full_name: string;
  student_id: string; // kept as text to preserve leading zeros
  department: Department;
  semester: number; // 1 to 24
  cgpa: number; // 0.00 to 4.00
  headline: string;
  bio: string; // shown to users as "About Me"
  subjects: string[]; // subjects the tutor can teach (at least one)
  teaching_mode: TeachingMode;
  hourly_rate: number | null; // in BDT; null means "not specified"
  tutoring_experience: TutoringExperience;
  profile_image_url: string | null; // public URL of the stored image, if any
  created_at: string; // ISO date-time string from the backend
  updated_at: string; // ISO date-time string from the backend
}

// The data the frontend sends when creating or updating a tutor. The backend
// generates id, created_at and updated_at itself.
export type TutorFormData = Omit<Tutor, "id" | "created_at" | "updated_at">;
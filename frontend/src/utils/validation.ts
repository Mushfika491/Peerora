import {
  MAX_SEMESTER,
  MIN_SEMESTER,
} from "../constants/tutorOptions";
import {
  isDepartment,
  isKnownSubject,
  isTeachingMode,
  isTutoringExperience,
} from "../types/tutor";
import type {
  Department,
  TeachingMode,
  Tutor,
  TutorFormData,
  TutoringExperience,
} from "../types/tutor";

// ===== Field rules (shared with the form for counters and file inputs) =====
export const FULL_NAME_MIN_LENGTH = 2;
export const FULL_NAME_MAX_LENGTH = 100;
export const STUDENT_ID_LENGTH = 7;
export const HEADLINE_MAX_LENGTH = 100;
export const BIO_MAX_LENGTH = 500;
export const CGPA_MIN = 0;
export const CGPA_MAX = 4;

// ===== Profile picture rules =====
export const ALLOWED_IMAGE_TYPES: readonly string[] = [
  "image/jpeg", // covers both .jpg and .jpeg files
  "image/png",
  "image/webp",
];
export const MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024; // 2 MB
// Value for the "accept" attribute of the file input (Group 2).
export const IMAGE_ACCEPT_ATTRIBUTE =
  ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp";

// ===== Form types =====

// HTML inputs give text, so numeric fields are strings while the user types.
// Fixed-choice fields are "" until the user selects an option.
export interface TutorFormValues {
  full_name: string;
  student_id: string;
  department: Department | "";
  semester: string;
  cgpa: string;
  headline: string;
  bio: string;
  subjects: string[];
  teaching_mode: TeachingMode | "";
  hourly_rate: string;
  tutoring_experience: TutoringExperience | "";
  profile_image_file: File | null; // a newly chosen file, not yet uploaded
  profile_image_url: string; // an already saved image address ("" if none)
}

// One optional error message per field.
export type TutorFormErrors = Partial<Record<keyof TutorFormValues, string>>;

// Starting values for the "create" form. Treat these as read-only: always
// create new objects and arrays when updating state.
export const EMPTY_TUTOR_FORM_VALUES: TutorFormValues = {
  full_name: "",
  student_id: "",
  department: "",
  semester: "",
  cgpa: "",
  headline: "",
  bio: "",
  subjects: [],
  teaching_mode: "",
  hourly_rate: "",
  tutoring_experience: "",
  profile_image_file: null,
  profile_image_url: "",
};

// ===== Helpers =====

// Counts characters the same way Python's len() does (emoji count as one).
// The form's live character counters should use this too.
export function countCharacters(text: string): number {
  return Array.from(text).length;
}

// ===== Validation helpers (each returns an error message, or undefined if valid) =====

function checkText(
  value: string,
  label: string,
  maxLength: number,
  minLength = 1
): string | undefined {
  const text = value.trim();

  if (text === "") {
    return `${label} is required.`;
  }

  const length = countCharacters(text);
  if (length < minLength) {
    return `${label} must be at least ${minLength} characters.`;
  }
  if (length > maxLength) {
    return `${label} must be at most ${maxLength} characters (currently ${length}).`;
  }
  return undefined;
}

// Only the length is checked. No other ID format rule is applied, and a valid
// length does not mean the student has been verified.
function checkStudentId(value: string): string | undefined {
  const text = value.trim();

  if (text === "") {
    return "University Student ID is required.";
  }

  const length = countCharacters(text);
  if (length !== STUDENT_ID_LENGTH) {
    return `University Student ID must be exactly ${STUDENT_ID_LENGTH} characters (you entered ${length}).`;
  }
  return undefined;
}

function checkSemester(value: string): string | undefined {
  const text = value.trim();

  if (text === "") {
    return "Please select your current semester.";
  }

  const semester = Number(text);
  if (!/^\d+$/.test(text) || semester < MIN_SEMESTER || semester > MAX_SEMESTER) {
    return `Semester must be a whole number from ${MIN_SEMESTER} to ${MAX_SEMESTER}.`;
  }
  return undefined;
}

function checkCgpa(value: string): string | undefined {
  const text = value.trim();
  const rangeMessage = "CGPA must be between 0.00 and 4.00.";

  if (text === "") {
    return "CGPA is required.";
  }
  if (!/^-?\d+(\.\d+)?$/.test(text)) {
    return "CGPA must be a number (for example 3.75).";
  }
  if (text.startsWith("-")) {
    return rangeMessage;
  }

  const cgpa = Number(text);
  if (cgpa < CGPA_MIN || cgpa > CGPA_MAX) {
    return rangeMessage;
  }
  if (!/^\d+(\.\d{1,2})?$/.test(text)) {
    return "CGPA can have at most 2 decimal places.";
  }
  return undefined;
}

// The hourly rate is optional. There is no maximum, only "not negative".
function checkHourlyRate(value: string): string | undefined {
  const text = value.trim();

  if (text === "") {
    return undefined;
  }
  if (!/^-?\d+(\.\d+)?$/.test(text)) {
    return "Hourly rate must be a number (for example 500 or 500.50).";
  }
  if (text.startsWith("-")) {
    return "Hourly rate cannot be negative.";
  }
  if (!/^\d+(\.\d{1,2})?$/.test(text)) {
    return "Hourly rate can have at most 2 decimal places.";
  }
  if (!Number.isFinite(Number(text))) {
    return "Hourly rate is too large.";
  }
  return undefined;
}

function checkSubjects(subjects: string[]): string | undefined {
  if (subjects.length === 0) {
    return "Please select at least one subject you can tutor.";
  }
  if (!subjects.every((subject) => isKnownSubject(subject))) {
    return "One or more selected subjects are not valid. Please choose from the list.";
  }
  if (new Set(subjects).size !== subjects.length) {
    return "The same subject was selected more than once.";
  }
  return undefined;
}

// Validates a profile picture file (format and size). Returns undefined if valid.
export function validateProfileImage(file: File): string | undefined {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return "Profile picture must be a JPG, JPEG, PNG, or WebP image.";
  }
  if (file.size === 0) {
    return "Profile picture file is empty.";
  }
  if (file.size > MAX_IMAGE_SIZE_BYTES) {
    return "Profile picture must be 2 MB or smaller.";
  }
  return undefined;
}

// Adds a message to the errors object only when a message exists.
function addError(
  errors: TutorFormErrors,
  field: keyof TutorFormValues,
  message: string | undefined
): void {
  if (message !== undefined) {
    errors[field] = message;
  }
}

// ===== Public functions =====

// Checks every field and returns all errors found. An empty object means valid.
export function validateTutorForm(values: TutorFormValues): TutorFormErrors {
  const errors: TutorFormErrors = {};

  // A. Personal and academic information
  addError(
    errors,
    "full_name",
    checkText(values.full_name, "Full name", FULL_NAME_MAX_LENGTH, FULL_NAME_MIN_LENGTH)
  );
  addError(errors, "student_id", checkStudentId(values.student_id));

  if (!isDepartment(values.department)) {
    errors.department = "Please select a department.";
  }

  addError(errors, "semester", checkSemester(values.semester));
  addError(errors, "cgpa", checkCgpa(values.cgpa));

  if (values.profile_image_file !== null) {
    addError(errors, "profile_image_file", validateProfileImage(values.profile_image_file));
  }

  // B. Tutoring information
  addError(errors, "headline", checkText(values.headline, "Headline", HEADLINE_MAX_LENGTH));
  addError(errors, "subjects", checkSubjects(values.subjects));

  if (!isTeachingMode(values.teaching_mode)) {
    errors.teaching_mode = "Please select a teaching mode.";
  }

  addError(errors, "hourly_rate", checkHourlyRate(values.hourly_rate));

  // C. Teaching experience
  if (!isTutoringExperience(values.tutoring_experience)) {
    errors.tutoring_experience = "Please select your previous tutoring experience.";
  }

  // D. About me
  addError(errors, "bio", checkText(values.bio, "About Me", BIO_MAX_LENGTH));

  return errors;
}

export function hasErrors(errors: TutorFormErrors): boolean {
  return Object.keys(errors).length > 0;
}

// Converts validated form text into the object sent to the API.
// Call this only after validateTutorForm reported no errors.
// "profileImageUrl" is the final public address of the picture (or null); the
// caller decides it, because a newly chosen file must be uploaded first.
export function toTutorFormData(
  values: TutorFormValues,
  profileImageUrl: string | null
): TutorFormData {
  if (!isDepartment(values.department)) {
    throw new Error("Cannot convert the form: no valid department selected.");
  }
  if (!isTeachingMode(values.teaching_mode)) {
    throw new Error("Cannot convert the form: no valid teaching mode selected.");
  }
  if (!isTutoringExperience(values.tutoring_experience)) {
    throw new Error("Cannot convert the form: no valid tutoring experience selected.");
  }

  const hourlyRateText = values.hourly_rate.trim();

  return {
    full_name: values.full_name.trim(),
    student_id: values.student_id.trim(),
    department: values.department,
    semester: Number(values.semester.trim()),
    cgpa: Number(values.cgpa.trim()),
    headline: values.headline.trim(),
    bio: values.bio.trim(),
    subjects: [...values.subjects],
    teaching_mode: values.teaching_mode,
    hourly_rate: hourlyRateText === "" ? null : Number(hourlyRateText),
    tutoring_experience: values.tutoring_experience,
    profile_image_url: profileImageUrl,
  };
}

// Converts an existing tutor from the API into form values (used by the edit page).
export function tutorToFormValues(tutor: Tutor): TutorFormValues {
  return {
    full_name: tutor.full_name,
    student_id: tutor.student_id,
    department: tutor.department,
    semester: String(tutor.semester),
    cgpa: tutor.cgpa.toFixed(2),
    headline: tutor.headline,
    bio: tutor.bio,
    subjects: [...tutor.subjects],
    teaching_mode: tutor.teaching_mode,
    hourly_rate: tutor.hourly_rate === null ? "" : String(tutor.hourly_rate),
    tutoring_experience: tutor.tutoring_experience,
    profile_image_file: null,
    profile_image_url: tutor.profile_image_url ?? "",
  };
}
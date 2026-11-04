
import { ApiError, apiDelete, apiGet, apiPost, apiPut } from "./apiClient";
import {
  isDepartment,
  isTeachingMode,
  isTutoringExperience,
} from "../types/tutor";
import type { Tutor, TutorFormData, TutorId } from "../types/tutor";

// Backend path for the tutor resource. The base URL comes from apiClient.
const TUTORS_PATH = "/tutors";

const INVALID_DATA_MESSAGE =
  "The server returned data in an unexpected format.";

// ---- Response validation ----

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.every((item: unknown) => typeof item === "string")
  );
}

// Runtime check that an unknown value really has every field of a Tutor.
function isTutor(value: unknown): value is Tutor {
  if (!isRecord(value)) {
    return false;
  }

  return (
    (typeof value.id === "number" || typeof value.id === "string") &&
    typeof value.full_name === "string" &&
    typeof value.student_id === "string" &&
    isDepartment(value.department) &&
    typeof value.semester === "number" &&
    typeof value.cgpa === "number" &&
    typeof value.headline === "string" &&
    typeof value.bio === "string" &&
    isStringArray(value.subjects) &&
    isTeachingMode(value.teaching_mode) &&
    (value.hourly_rate === null || typeof value.hourly_rate === "number") &&
    isTutoringExperience(value.tutoring_experience) &&
    (value.profile_image_url === null ||
      typeof value.profile_image_url === "string") &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string"
  );
}

function parseTutor(data: unknown): Tutor {
  if (!isTutor(data)) {
    throw new ApiError(INVALID_DATA_MESSAGE);
  }
  return data;
}

function parseTutorList(data: unknown): Tutor[] {
  if (!Array.isArray(data)) {
    throw new ApiError(INVALID_DATA_MESSAGE);
  }

  const items: unknown[] = data;
  const tutors: Tutor[] = [];

  for (const item of items) {
    if (!isTutor(item)) {
      throw new ApiError(INVALID_DATA_MESSAGE);
    }
    tutors.push(item);
  }

  return tutors;
}

// Builds "/tutors/<id>", encoding the id so special characters are safe.
function tutorPath(id: TutorId): string {
  return `${TUTORS_PATH}/${encodeURIComponent(String(id))}`;
}

// ---- The five CRUD operations ----

// READ (list): GET /tutors
export async function getTutors(): Promise<Tutor[]> {
  const data = await apiGet(TUTORS_PATH);
  return parseTutorList(data);
}

// READ (single): GET /tutors/{id}
export async function getTutorById(id: TutorId): Promise<Tutor> {
  const data = await apiGet(tutorPath(id));
  return parseTutor(data);
}

// CREATE: POST /tutors
export async function createTutor(formData: TutorFormData): Promise<Tutor> {
  const data = await apiPost(TUTORS_PATH, formData);
  return parseTutor(data);
}

// UPDATE: PUT /tutors/{id}
export async function updateTutor(
  id: TutorId,
  formData: TutorFormData
): Promise<Tutor> {
  const data = await apiPut(tutorPath(id), formData);
  return parseTutor(data);
}

// DELETE: DELETE /tutors/{id}
export async function deleteTutor(id: TutorId): Promise<void> {
  await apiDelete(tutorPath(id));
}

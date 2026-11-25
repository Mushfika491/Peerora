import { ApiError, apiDelete, apiGet, apiGetWithTotal, apiPost, apiPut, toQuery } from "./apiClient";
import {
  isDepartment,
  isTeachingMode,
  isTutoringExperience,
} from "../types/tutor";
import type { Tutor, TutorFormData, TutorId } from "../types/tutor";

// Backend path for the tutor resource. The base URL comes from apiClient.
const TUTORS_PATH = "/api/tutors";

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
    typeof value.id === "number" &&
    (value.user_id === null || typeof value.user_id === "number") &&
    typeof value.full_name === "string" &&
    // The Student ID is private: only the owner and administrators receive it.
    (value.student_id === undefined || typeof value.student_id === "string") &&
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

// Builds "/api/tutors/<id>", encoding the id so special characters are safe.
function tutorPath(id: TutorId): string {
  return `${TUTORS_PATH}/${encodeURIComponent(String(id))}`;
}

// ---- The five CRUD operations ----

export interface TutorSearch {
  q?: string;
  subject?: string;
  department?: string;
  teaching_mode?: string;
  limit?: number;
  offset?: number;
}

// READ (list): GET /api/tutors?q=&subject=&... (filters run on the server)
export async function getTutors(search: TutorSearch = {}): Promise<Tutor[]> {
  return (await searchTutors(search)).tutors;
}

// Same as getTutors, plus the total number of matches for pagination.
export async function searchTutors(
  search: TutorSearch = {}
): Promise<{ tutors: Tutor[]; total: number }> {
  const { data, total } = await apiGetWithTotal(`${TUTORS_PATH}${toQuery({ ...search })}`);
  const tutors = parseTutorList(data);
  return { tutors, total: total ?? tutors.length };
}

// READ (own profile): GET /api/tutors/me. Returns null when none exists yet.
export async function getMyTutorProfile(): Promise<Tutor | null> {
  try {
    return parseTutor(await apiGet(`${TUTORS_PATH}/me`));
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

// READ (single): GET /api/tutors/{id}
export async function getTutorById(id: TutorId): Promise<Tutor> {
  const data = await apiGet(tutorPath(id));
  return parseTutor(data);
}

// CREATE: POST /api/tutors
export async function createTutor(formData: TutorFormData): Promise<Tutor> {
  const data = await apiPost(TUTORS_PATH, formData);
  return parseTutor(data);
}

// UPDATE: PUT /api/tutors/{id}
export async function updateTutor(
  id: TutorId,
  formData: TutorFormData
): Promise<Tutor> {
  const data = await apiPut(tutorPath(id), formData);
  return parseTutor(data);
}

// DELETE: DELETE /api/tutors/{id}
export async function deleteTutor(id: TutorId): Promise<void> {
  await apiDelete(tutorPath(id));
}

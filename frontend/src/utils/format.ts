import {
  TEACHING_MODE_OPTIONS,
  TUTORING_EXPERIENCE_OPTIONS,
} from "../constants/tutorOptions";
import type { TeachingMode, TutoringExperience } from "../types/tutor";

// "Amina Rahman" -> "AR"
export function getInitials(fullName: string): string {
  const words = fullName
    .trim()
    .split(/\s+/)
    .filter((word) => word !== "");
  const initials = words.slice(0, 2).map((word) => word.charAt(0).toUpperCase());
  return initials.join("");
}

// "in_person" -> "In-person"
export function getTeachingModeLabel(mode: TeachingMode): string {
  const option = TEACHING_MODE_OPTIONS.find((item) => item.value === mode);
  return option !== undefined ? option.label : mode;
}

// "under_6_months" -> "Less than 6 months"
export function getTutoringExperienceLabel(
  experience: TutoringExperience
): string {
  const option = TUTORING_EXPERIENCE_OPTIONS.find(
    (item) => item.value === experience
  );
  return option !== undefined ? option.label : experience;
}

// 3.5 -> "3.50"
export function formatCgpa(cgpa: number): string {
  return cgpa.toFixed(2);
}

// 5 -> "Semester 5"
export function formatSemester(semester: number): string {
  return `Semester ${semester}`;
}

// 1500 -> "BDT 1,500 / hour"; null -> "Not specified"
export function formatHourlyRate(rate: number | null): string {
  if (rate === null) {
    return "Not specified";
  }
  const amount = rate.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  return `BDT ${amount} / hour`;
}

// "2026-11-01T10:00:00" -> "1 November 2026". Returns the original text if invalid.
export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return isoString;
  }
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}
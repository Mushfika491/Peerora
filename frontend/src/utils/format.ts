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

// ---- Dates and times ----
// The API sends timestamps in UTC (ISO 8601 with "Z" or "+00:00"). They are
// shown in the viewer's own timezone by the browser's Intl API; nothing here
// adds a fixed offset. Pass `timeZone` only to override that (e.g. in tests).

const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;
const HAS_ZONE = /(Z|[+-]\d{2}:?\d{2})$/i;

// Parses an API timestamp. A value without a timezone is treated as UTC
// (that is how the backend stores every timestamp), never as local time.
export function parseApiDate(isoString: string): Date | null {
  const text = isoString.trim();
  const normalized = DATE_ONLY.test(text) || HAS_ZONE.test(text) ? text : `${text}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

// "2026-11-01T10:00:00Z" -> "1 November 2026" (in the viewer's timezone).
// A date-only value such as a due date ("2026-11-28") is a calendar date and
// is shown as that same day everywhere. Returns the original text if invalid.
export function formatDate(isoString: string, timeZone?: string): string {
  const date = parseApiDate(isoString);
  if (date === null) {
    return isoString;
  }
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: DATE_ONLY.test(isoString.trim()) ? "UTC" : timeZone,
  });
}

// "2026-11-24T00:37:00Z" -> "24 Nov 2026, 06:37" for a viewer in Bangladesh
// (UTC+6), "23 Nov 2026, 19:37" in New York, and so on. Returns the original
// text if invalid, and "never" for null.
export function formatDateTime(isoString: string | null, timeZone?: string): string {
  if (isoString === null) {
    return "never";
  }
  const date = parseApiDate(isoString);
  if (date === null) {
    return isoString;
  }
  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  });
}

// The viewer's timezone, e.g. "Asia/Dhaka" (shown next to times in the admin pages).
export function localTimeZoneName(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "local time";
}

// ---- Browser identification ----
// Order matters: Edge, Opera and Brave all contain "Chrome/" too, and Chrome
// contains "Safari/". Brave normally sends Chrome's exact User-Agent; the
// backend adds a "Brave" token when the browser's client hints or the
// frontend's navigator.brave check say it is Brave (see
// backend/peerora/core/request_info.py). Without that token Brave cannot be
// told apart from Chrome, so it is shown as Chrome - never the other way round.
export function identifyBrowser(userAgent: string | null): string {
  if (userAgent === null || userAgent.trim() === "") {
    return "Unknown browser";
  }
  if (/\bBrave\b/.test(userAgent)) return "Brave";
  if (/\bEdg(e|A|iOS)?\//.test(userAgent)) return "Edge";
  if (/\b(OPR|Opera)\//.test(userAgent)) return "Opera";
  if (/\bSamsungBrowser\//.test(userAgent)) return "Samsung Internet";
  if (/\b(Firefox|FxiOS)\//.test(userAgent)) return "Firefox";
  if (/\b(Chrome|CriOS)\//.test(userAgent)) return "Chrome";
  if (/\bChromium\//.test(userAgent)) return "Chromium";
  if (/\bVersion\/[\d.]+.*\bSafari\//.test(userAgent)) return "Safari";
  return "Unknown browser";
}

export function identifySystem(userAgent: string | null): string {
  if (userAgent === null) return "";
  if (/Windows/.test(userAgent)) return "Windows";
  if (/Android/.test(userAgent)) return "Android";
  if (/iPhone|iPad|iPod/.test(userAgent)) return "iOS";
  if (/Mac OS X|Macintosh/.test(userAgent)) return "macOS";
  if (/CrOS/.test(userAgent)) return "ChromeOS";
  if (/Linux/.test(userAgent)) return "Linux";
  return "";
}

// A short, readable description, e.g. "Brave on Linux".
export function describeUserAgent(userAgent: string | null): string {
  if (userAgent === null || userAgent.trim() === "") {
    return "Unknown device";
  }
  const browser = identifyBrowser(userAgent);
  const system = identifySystem(userAgent);
  return system === "" ? browser : `${browser} on ${system}`;
}

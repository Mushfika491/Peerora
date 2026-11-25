import { ApiError } from "./apiClient";

// Minimal runtime checks for API responses. The backend is trusted to send
// the documented shape; these checks catch a wrong URL or a broken proxy
// (e.g. an HTML page instead of JSON) with a clear message.
const INVALID = "The server returned data in an unexpected format.";

export function expectObject<T>(data: unknown, requiredKeys: string[]): T {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new ApiError(INVALID);
  }
  for (const key of requiredKeys) {
    if (!(key in data)) {
      throw new ApiError(INVALID);
    }
  }
  return data as T;
}

export function expectArray<T>(data: unknown, requiredKeys: string[]): T[] {
  if (!Array.isArray(data)) {
    throw new ApiError(INVALID);
  }
  return data.map((item: unknown) => expectObject<T>(item, requiredKeys));
}

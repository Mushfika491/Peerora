// Read the backend URL from the Vite environment variable (see .env).
// The value is typed as "unknown" and checked, instead of trusting it blindly.
const rawBaseUrl: unknown = import.meta.env.VITE_API_BASE_URL;

// Remove spaces and any trailing slashes, e.g. "http://localhost:8000/" becomes
// "http://localhost:8000". An empty string means the variable is not set.
const API_BASE_URL: string =
  typeof rawBaseUrl === "string" ? rawBaseUrl.trim().replace(/\/+$/, "") : "";

// A custom error class so components can show a clear message and, if
// needed, check the HTTP status code (null means no response was received).
export class ApiError extends Error {
  readonly status: number | null;

  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Tries to read a readable message from a failed response.
// FastAPI sends errors as { "detail": "text" } or, for validation errors
// (status 422), { "detail": [ { "msg": "text", ... }, ... ] }.
async function readErrorMessage(response: Response): Promise<string> {
  const fallback = `The request failed with status ${response.status}.`;

  try {
    const body: unknown = await response.json();

    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail: unknown = body.detail;

      if (typeof detail === "string") {
        return detail;
      }

      if (Array.isArray(detail)) {
        const items: unknown[] = detail;
        const messages: string[] = [];

        for (const item of items) {
          if (
            typeof item === "object" &&
            item !== null &&
            "msg" in item &&
            typeof item.msg === "string"
          ) {
            messages.push(item.msg);
          }
        }

        if (messages.length > 0) {
          return messages.join(" ");
        }
      }
    }
  } catch {
    // The error body was not valid JSON; use the fallback message below.
  }

  return fallback;
}

// Sends the request and throws an ApiError if the server cannot be reached
// or answers with an unsuccessful status (anything outside 200-299).
async function sendRequest(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  if (API_BASE_URL === "") {
    throw new ApiError(
      "The API base URL is not configured. Set VITE_API_BASE_URL in your .env file and restart the development server."
    );
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    // fetch only rejects on network-level failures (server down, CORS block, no internet).
    throw new ApiError(
      "Unable to reach the server. Check that the backend is running and that the API URL is correct."
    );
  }

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status);
  }

  return response;
}

// Converts the response body to JSON. The result is "unknown" on purpose:
// the service layer must validate its shape before using it.
async function parseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new ApiError(
      "The server returned an invalid response (not valid JSON).",
      response.status
    );
  }
}

// ---- Public helper functions, one per HTTP method ----

export async function apiGet(path: string): Promise<unknown> {
  const response = await sendRequest(path, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  return parseJson(response);
}

export async function apiPost(path: string, body: unknown): Promise<unknown> {
  const response = await sendRequest(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });
  return parseJson(response);
}

export async function apiPut(path: string, body: unknown): Promise<unknown> {
  const response = await sendRequest(path, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });
  return parseJson(response);
}

// DELETE does not need the response body, so nothing is parsed.
export async function apiDelete(path: string): Promise<void> {
  await sendRequest(path, { method: "DELETE" });
}
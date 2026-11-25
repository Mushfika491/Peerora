// Shared HTTP client used by every service module.
//
// Authentication:
// - The short-lived access token is kept in memory only (never in
//   localStorage), and sent as "Authorization: Bearer <token>".
// - The refresh token lives in an HttpOnly cookie that JavaScript cannot read.
// - When a request answers 401, the client asks AuthContext to refresh the
//   session once and repeats the request with the new access token.

import { CLIENT_BRAND_HEADER, detectClientBrand } from "./clientBrand";

// The API base URL. Empty (the default) means "same origin": in production
// Vercel serves the API under /api, and in development Vite proxies /api to
// the backend (see vite.config.ts).
// Every request path already starts with "/api/", so a trailing "/api" in the
// setting (e.g. an older "/api" value) is dropped instead of doubling the path.
export function normalizeApiBaseUrl(raw: unknown): string {
  if (typeof raw !== "string") {
    return "";
  }
  return raw.trim().replace(/\/+$/, "").replace(/\/api$/, "");
}

const API_BASE_URL: string = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

// Sent on cookie-authenticated requests (refresh/logout) as CSRF protection.
export const CSRF_HEADERS = { "X-Requested-With": "peerora" };

// A custom error class so components can show a clear message and, if
// needed, check the HTTP status code (null means no response was received)
// and the backend's machine-readable error code (X-Error-Code header).
export class ApiError extends Error {
  readonly status: number | null;
  readonly code: string | null;

  constructor(message: string, status: number | null = null, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

// The backend marks "your account is suspended" 403 responses with this code.
// Only these sign the user out; ordinary 403s ("you cannot edit this") do not.
export const ACCOUNT_SUSPENDED_CODE = "account_suspended";

export function isAccountSuspended(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403 && error.code === ACCOUNT_SUSPENDED_CODE;
}

// ---- Access token and refresh hook (set by AuthContext) ----

let accessToken: string | null = null;
let refreshHandler: (() => Promise<string | null>) | null = null;
let suspendedHandler: ((message: string) => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setRefreshHandler(handler: (() => Promise<string | null>) | null): void {
  refreshHandler = handler;
}

// Called when a signed-in request is refused because the account was banned.
export function setSuspendedHandler(handler: ((message: string) => void) | null): void {
  suspendedHandler = handler;
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

interface RequestSettings {
  // false for the auth endpoints themselves, so a failed refresh never loops.
  retryOnUnauthorized?: boolean;
}

// Sends the request and throws an ApiError if the server cannot be reached
// or answers with an unsuccessful status (anything outside 200-299).
export async function sendRequest(
  path: string,
  options: RequestInit = {},
  settings: RequestSettings = {}
): Promise<Response> {
  const { retryOnUnauthorized = true } = settings;
  // "Brave" when navigator.brave confirms it (for the activity log), else null.
  const clientBrand = await detectClientBrand();

  const buildInit = (): RequestInit => {
    const headers = new Headers(options.headers);
    if (accessToken !== null && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
    if (clientBrand !== null) {
      headers.set(CLIENT_BRAND_HEADER, clientBrand);
    }
    return { ...options, headers, credentials: "include" };
  };

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, buildInit());
    if (response.status === 401 && retryOnUnauthorized && refreshHandler !== null) {
      const newToken = await refreshHandler();
      if (newToken !== null) {
        response = await fetch(`${API_BASE_URL}${path}`, buildInit());
      }
    }
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // fetch only rejects on network-level failures (server down, CORS block, no internet).
    throw new ApiError(
      "Unable to reach the server. Check your connection and try again."
    );
  }

  if (!response.ok) {
    const error = new ApiError(
      await readErrorMessage(response),
      response.status,
      response.headers.get("X-Error-Code")
    );
    // A banned account: end the session in the browser too. The auth endpoints
    // (retryOnUnauthorized=false) report this themselves, e.g. on the login form.
    if (retryOnUnauthorized && isAccountSuspended(error) && suspendedHandler !== null) {
      suspendedHandler(error.message);
    }
    throw error;
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

// GET that also returns the X-Total-Count header (used for paginated lists).
export async function apiGetWithTotal(
  path: string
): Promise<{ data: unknown; total: number | null }> {
  const response = await sendRequest(path, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  const header = response.headers.get("X-Total-Count");
  const total = header === null ? null : Number(header);
  return { data: await parseJson(response), total: Number.isFinite(total) ? total : null };
}

function jsonRequest(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  };
}

export async function apiPost(path: string, body?: unknown): Promise<unknown> {
  return parseJson(await sendRequest(path, jsonRequest("POST", body)));
}

export async function apiPut(path: string, body: unknown): Promise<unknown> {
  return parseJson(await sendRequest(path, jsonRequest("PUT", body)));
}

export async function apiPatch(path: string, body: unknown): Promise<unknown> {
  return parseJson(await sendRequest(path, jsonRequest("PATCH", body)));
}

// POST without a JSON response body (204 No Content).
export async function apiPostNoContent(path: string, body?: unknown): Promise<void> {
  await sendRequest(path, jsonRequest("POST", body));
}

// DELETE does not need the response body, so nothing is parsed.
export async function apiDelete(path: string): Promise<void> {
  await sendRequest(path, { method: "DELETE" });
}

// Downloads a file (CSV export) with the access token and saves it.
// A plain <a href> cannot send the Authorization header, so the file is
// fetched first and then handed to the browser as a temporary blob URL.
export async function apiDownload(path: string, fallbackName: string): Promise<void> {
  const response = await sendRequest(path, { method: "GET" });
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="([^"]+)"/.exec(disposition);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = match?.[1] ?? fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// Builds "?a=1&b=x" from an object, skipping empty values.
export function toQuery(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const text = search.toString();
  return text === "" ? "" : `?${text}`;
}

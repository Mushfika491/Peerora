import { CSRF_HEADERS, sendRequest } from "./apiClient";
import { expectObject } from "./validate";
import type { SignupData, TokenResponse } from "../types/auth";

const TOKEN_KEYS = ["access_token", "expires_in", "user"];

async function tokenRequest(path: string, body?: unknown): Promise<TokenResponse> {
  const response = await sendRequest(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json", ...CSRF_HEADERS },
      body: body === undefined ? undefined : JSON.stringify(body),
    },
    { retryOnUnauthorized: false }
  );
  return expectObject<TokenResponse>(await response.json(), TOKEN_KEYS);
}

export function signup(data: SignupData): Promise<TokenResponse> {
  return tokenRequest("/api/auth/signup", data);
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return tokenRequest("/api/auth/login", { email, password });
}

// Only one refresh may run at a time. Two parallel refreshes would present the
// same refresh token twice, which the backend treats as token theft (reuse)
// and answers by ending the session.
// - Within one tab, every caller shares the same promise.
// - Across tabs, the Web Locks API makes tabs take turns, so the second tab
//   sends the cookie the first tab just received. (The backend also tolerates
//   a repeat within a few seconds, for browsers without Web Locks.)
let refreshInFlight: Promise<TokenResponse> | null = null;
const REFRESH_LOCK_NAME = "peerora-token-refresh";

function withCrossTabLock<T>(task: () => Promise<T>): Promise<T> {
  const locks = typeof navigator !== "undefined" ? navigator.locks : undefined;
  if (locks === undefined || typeof locks.request !== "function") {
    return task();
  }
  return locks.request(REFRESH_LOCK_NAME, task) as Promise<T>;
}

export function refresh(): Promise<TokenResponse> {
  if (refreshInFlight === null) {
    refreshInFlight = withCrossTabLock(() => tokenRequest("/api/auth/refresh")).finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

export async function logout(): Promise<void> {
  await sendRequest(
    "/api/auth/logout",
    { method: "POST", headers: CSRF_HEADERS },
    { retryOnUnauthorized: false }
  );
}

// ---- Forgotten password ----
// These are public endpoints (no access token, no retry on 401).

export interface ResetAvailability {
  available: boolean;
  token_minutes: number;
}

async function publicJson(path: string, init: RequestInit): Promise<unknown> {
  const response = await sendRequest(path, init, { retryOnUnauthorized: false });
  return response.json();
}

export async function getPasswordResetAvailability(): Promise<ResetAvailability> {
  return expectObject<ResetAvailability>(
    await publicJson("/api/auth/password-reset/availability", { method: "GET", headers: { Accept: "application/json" } }),
    ["available", "token_minutes"]
  );
}

// Always resolves with the same generic message, whether or not the email has an account.
export async function requestPasswordReset(email: string): Promise<string> {
  const data = expectObject<{ detail: string }>(
    await publicJson("/api/auth/password-reset/request", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ email }),
    }),
    ["detail"]
  );
  return data.detail;
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<string> {
  const data = expectObject<{ detail: string }>(
    await publicJson("/api/auth/password-reset/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    }),
    ["detail"]
  );
  return data.detail;
}

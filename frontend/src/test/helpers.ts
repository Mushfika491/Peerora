import type { TokenResponse, User } from "../types/auth";

export function makeUser(changes: Partial<User> = {}): User {
  return {
    id: 1,
    email: "student@example.com",
    full_name: "Sam Student",
    account_type: "student",
    role: "user",
    created_at: "2026-11-01T10:00:00Z",
    has_tutor_profile: false,
    ...changes,
  };
}

export function tokenResponse(user: User, token = "access-1"): TokenResponse {
  return { access_token: token, token_type: "bearer", expires_in: 900, user };
}

export function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

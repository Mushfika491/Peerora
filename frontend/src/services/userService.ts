import { apiDelete, apiGet, apiPatch, apiPostNoContent } from "./apiClient";
import { expectArray, expectObject } from "./validate";
import type { SessionInfo, User } from "../types/auth";

const USER_KEYS = ["id", "email", "full_name", "account_type", "role"];

export async function getMe(): Promise<User> {
  return expectObject<User>(await apiGet("/api/users/me"), USER_KEYS);
}

export async function updateProfile(changes: {
  full_name?: string;
  email?: string;
  current_password?: string;
}): Promise<User> {
  return expectObject<User>(await apiPatch("/api/users/me", changes), USER_KEYS);
}

export function changePassword(current_password: string, new_password: string): Promise<void> {
  return apiPostNoContent("/api/users/me/password", { current_password, new_password });
}

export async function getSessions(): Promise<SessionInfo[]> {
  return expectArray<SessionInfo>(await apiGet("/api/users/me/sessions"), ["id", "is_current"]);
}

export function revokeSession(sessionId: string): Promise<void> {
  return apiDelete(`/api/users/me/sessions/${encodeURIComponent(sessionId)}`);
}

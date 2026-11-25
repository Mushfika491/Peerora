import { apiDelete, apiDownload, apiGet, apiPatch, apiPost, toQuery } from "./apiClient";
import { expectObject } from "./validate";
import type {
  AdminGroup,
  AdminGroupDetail,
  AdminRecord,
  AdminUser,
  AdminUserDetail,
  AuditLog,
  BulkResult,
  Overview,
  Page,
  SecurityReport,
} from "../types/admin";

type Query = Record<string, string | number | null | undefined>;

const PAGE_KEYS = ["items", "total", "page", "page_size"];

async function getPage<T>(path: string, query: Query): Promise<Page<T>> {
  return expectObject<Page<T>>(await apiGet(`${path}${toQuery(query)}`), PAGE_KEYS);
}

export async function getOverview(): Promise<Overview> {
  return expectObject<Overview>(await apiGet("/api/admin/overview"), ["total_users"]);
}

// ---- Users ----
export const listUsers = (query: Query) => getPage<AdminUser>("/api/admin/users", query);

export async function getUserDetail(id: number): Promise<AdminUserDetail> {
  return expectObject<AdminUserDetail>(await apiGet(`/api/admin/users/${id}`), ["user", "active_sessions"]);
}

export async function banUser(id: number, reason: string): Promise<AdminUser> {
  return expectObject<AdminUser>(await apiPost(`/api/admin/users/${id}/ban`, { reason }), ["id"]);
}

export async function unbanUser(id: number, reason: string): Promise<AdminUser> {
  return expectObject<AdminUser>(await apiPost(`/api/admin/users/${id}/unban`, { reason }), ["id"]);
}

export async function bulkBan(user_ids: number[], reason: string): Promise<BulkResult> {
  return expectObject<BulkResult>(await apiPost("/api/admin/users/bulk-ban", { user_ids, reason }), ["done"]);
}

export async function bulkUnban(user_ids: number[], reason: string): Promise<BulkResult> {
  return expectObject<BulkResult>(await apiPost("/api/admin/users/bulk-unban", { user_ids, reason }), ["done"]);
}

export async function changeRole(id: number, role: "user" | "admin"): Promise<AdminUser> {
  return expectObject<AdminUser>(await apiPatch(`/api/admin/users/${id}/role`, { role }), ["id"]);
}

export function revokeUserSession(userId: number, sessionId: string): Promise<void> {
  return apiDelete(`/api/admin/users/${userId}/sessions/${encodeURIComponent(sessionId)}`);
}

export async function revokeAllUserSessions(userId: number): Promise<void> {
  await apiPost(`/api/admin/users/${userId}/sessions/revoke-all`);
}

// ---- Content moderation ----
export const listRecords = (query: Query) => getPage<AdminRecord>("/api/admin/records", query);
export const listGroups = (query: Query) => getPage<AdminGroup>("/api/admin/groups", query);

export async function getGroupDetail(id: number): Promise<AdminGroupDetail> {
  return expectObject<AdminGroupDetail>(await apiGet(`/api/admin/groups/${id}`), ["id", "members"]);
}

export async function deleteRecords(ids: number[]): Promise<BulkResult> {
  return expectObject<BulkResult>(await apiPost("/api/admin/records/bulk-delete", { ids }), ["done"]);
}

export async function deleteGroups(ids: number[]): Promise<BulkResult> {
  return expectObject<BulkResult>(await apiPost("/api/admin/groups/bulk-delete", { ids }), ["done"]);
}

// ---- Audit and security ----
export const listAuditLogs = (query: Query) => getPage<AuditLog>("/api/admin/audit-logs", query);

export async function getAuditActions(): Promise<string[]> {
  const data = await apiGet("/api/admin/audit-actions");
  return Array.isArray(data) ? data.filter((item): item is string => typeof item === "string") : [];
}

export async function getSecurityReport(hours: number): Promise<SecurityReport> {
  return expectObject<SecurityReport>(
    await apiGet(`/api/admin/security/failed-logins?hours=${hours}`),
    ["by_ip", "by_account", "recent"]
  );
}

// ---- CSV exports (use the same filters as the list on screen) ----
export function exportCsv(kind: "users" | "records" | "audit-logs", query: Query): Promise<void> {
  const { page: _page, page_size: _pageSize, ...filters } = query;
  void _page;
  void _pageSize;
  return apiDownload(`/api/admin/exports/${kind}.csv${toQuery(filters)}`, `peerora-${kind}.csv`);
}

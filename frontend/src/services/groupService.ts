import { apiDelete, apiGet, apiPatch, apiPost } from "./apiClient";
import { expectArray, expectObject } from "./validate";
import type {
  DashboardSummary,
  GroupInput,
  GroupMember,
  GroupPermissions,
  RecordInput,
  StudyGroup,
  StudyRecord,
} from "../types/group";

const GROUP_KEYS = ["id", "name", "my_role", "my_permissions", "member_count"];
const MEMBER_KEYS = ["user_id", "full_name", "group_role", "can_create_records", "can_update_records", "can_assign_records"];
const RECORD_KEYS = ["id", "title", "status", "can_edit", "can_assign", "can_delete"];

const groupPath = (id: number) => `/api/groups/${id}`;

// ---- Groups ----
export async function getMyGroups(): Promise<StudyGroup[]> {
  return expectArray<StudyGroup>(await apiGet("/api/groups"), GROUP_KEYS);
}

export async function getGroup(id: number): Promise<StudyGroup> {
  return expectObject<StudyGroup>(await apiGet(groupPath(id)), GROUP_KEYS);
}

export async function createGroup(data: GroupInput): Promise<StudyGroup> {
  return expectObject<StudyGroup>(await apiPost("/api/groups", data), GROUP_KEYS);
}

export async function updateGroup(id: number, data: Partial<GroupInput>): Promise<StudyGroup> {
  return expectObject<StudyGroup>(await apiPatch(groupPath(id), data), GROUP_KEYS);
}

export function deleteGroup(id: number): Promise<void> {
  return apiDelete(groupPath(id));
}

// ---- Members (owner manages; members may leave) ----
export type MemberPreset = "editor" | "viewer";

export async function getMembers(groupId: number): Promise<GroupMember[]> {
  return expectArray<GroupMember>(await apiGet(`${groupPath(groupId)}/members`), MEMBER_KEYS);
}

// Add a member with a preset; explicit permissions override the preset.
export async function addMember(
  groupId: number,
  email: string,
  group_role: MemberPreset,
  permissions: Partial<GroupPermissions> = {}
): Promise<GroupMember> {
  return expectObject<GroupMember>(
    await apiPost(`${groupPath(groupId)}/members`, { email, group_role, ...permissions }),
    MEMBER_KEYS
  );
}

// Change a member's permissions: a preset and/or individual permissions (owner only).
export async function updateMember(
  groupId: number,
  userId: number,
  changes: { group_role?: MemberPreset } & Partial<GroupPermissions>
): Promise<GroupMember> {
  return expectObject<GroupMember>(
    await apiPatch(`${groupPath(groupId)}/members/${userId}`, changes),
    MEMBER_KEYS
  );
}

export function removeMember(groupId: number, userId: number): Promise<void> {
  return apiDelete(`${groupPath(groupId)}/members/${userId}`);
}

// ---- Records ----
export async function getGroupRecords(groupId: number): Promise<StudyRecord[]> {
  return expectArray<StudyRecord>(await apiGet(`${groupPath(groupId)}/records`), RECORD_KEYS);
}

export async function createGroupRecord(groupId: number, data: RecordInput): Promise<StudyRecord> {
  return expectObject<StudyRecord>(await apiPost(`${groupPath(groupId)}/records`, data), RECORD_KEYS);
}

export async function getMyRecords(scope: "personal" | "assigned"): Promise<StudyRecord[]> {
  return expectArray<StudyRecord>(await apiGet(`/api/records?scope=${scope}`), RECORD_KEYS);
}

export async function createPersonalRecord(data: RecordInput): Promise<StudyRecord> {
  return expectObject<StudyRecord>(await apiPost("/api/records", data), RECORD_KEYS);
}

export async function updateRecord(id: number, data: Partial<RecordInput>): Promise<StudyRecord> {
  return expectObject<StudyRecord>(await apiPatch(`/api/records/${id}`, data), RECORD_KEYS);
}

export function deleteRecord(id: number): Promise<void> {
  return apiDelete(`/api/records/${id}`);
}

// ---- Dashboard ----
export async function getDashboardSummary(): Promise<DashboardSummary> {
  return expectObject<DashboardSummary>(await apiGet("/api/dashboard/summary"), ["groups", "record_counts"]);
}

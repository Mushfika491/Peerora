// The role is a label derived from the member's permissions:
// editor = all three, viewer = none, member = a custom mix. The owner has all.
export type GroupRole = "owner" | "editor" | "viewer" | "member";

export interface GroupPermissions {
  can_create_records: boolean;
  can_update_records: boolean;
  can_assign_records: boolean;
}

export type GroupPermission = keyof GroupPermissions;
export type RecordStatus = "todo" | "in_progress" | "done";

export interface StudyGroup {
  id: number;
  name: string;
  description: string | null;
  subject: string | null;
  owner_id: number;
  owner_name: string;
  my_role: GroupRole;
  my_permissions: GroupPermissions;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface GroupInput {
  name: string;
  description: string | null;
  subject: string | null;
}

export interface GroupMember extends GroupPermissions {
  user_id: number;
  full_name: string;
  email: string;
  group_role: GroupRole;
  joined_at: string;
}

export interface StudyRecord {
  id: number;
  title: string;
  content: string | null;
  status: RecordStatus;
  due_date: string | null;
  group_id: number | null;
  group_name: string | null;
  created_by_id: number;
  created_by_name: string;
  assigned_to_id: number | null;
  assigned_to_name: string | null;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
  can_assign: boolean;
  can_delete: boolean;
}

export interface RecordInput {
  title: string;
  content: string | null;
  status: RecordStatus;
  due_date: string | null;
  // Left out when the user may not assign (an unchanged assignee is not sent).
  assigned_to_id?: number | null;
}

export interface DashboardSummary {
  account_type: string;
  role: string;
  groups: StudyGroup[];
  group_count: number;
  record_counts: Record<RecordStatus, number>;
  assigned_to_me: StudyRecord[];
  personal_open: StudyRecord[];
  tutor_profile_id: number | null;
}

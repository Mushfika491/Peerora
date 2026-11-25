import type { SessionInfo } from "./auth";
import type { GroupMember } from "./group";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Overview {
  total_users: number;
  banned_users: number;
  admin_users: number;
  total_records: number;
  total_groups: number;
  total_tutor_profiles: number;
  new_users_last_7_days: number;
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  account_type: string;
  role: string;
  is_banned: boolean;
  ban_reason: string | null;
  banned_at: string | null;
  last_login_at: string | null;
  created_at: string;
}

export interface AdminRecord {
  id: number;
  title: string;
  status: string;
  group_id: number | null;
  group_name: string | null;
  created_by_id: number;
  created_by_name: string;
  created_by_email: string;
  assigned_to_name: string | null;
  created_at: string;
}

export interface AuditLog {
  id: number;
  action: string;
  actor_id: number | null;
  actor_email: string | null;
  target_user_id: number | null;
  target_user_email: string | null;
  target_type: string | null;
  target_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AdminUserDetail {
  user: AdminUser;
  tutor_profile_id: number | null;
  groups: { id: number; name: string; group_role: string }[];
  records: AdminRecord[];
  record_count: number;
  active_sessions: SessionInfo[];
  recent_activity: AuditLog[];
}

export interface AdminGroup {
  id: number;
  name: string;
  subject: string | null;
  owner_id: number;
  owner_name: string;
  owner_email: string;
  member_count: number;
  record_count: number;
  created_at: string;
}

export interface AdminGroupDetail extends AdminGroup {
  description: string | null;
  members: GroupMember[];
}

export interface BulkResult {
  results: { id: number; result: string }[];
  done: number;
}

export interface FailedLoginGroup {
  key: string;
  failures: number;
  last_attempt_at: string;
}

export interface SecurityReport {
  hours: number;
  total_failures: number;
  by_ip: FailedLoginGroup[];
  by_account: FailedLoginGroup[];
  recent: {
    email: string;
    ip_address: string | null;
    user_agent: string | null;
    failure_reason: string | null;
    created_at: string;
  }[];
}

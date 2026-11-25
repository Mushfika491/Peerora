// Account type = application experience (student or tutor dashboard).
// Role = security role checked by the backend (user or admin).
export type AccountType = "student" | "tutor";
export type SecurityRole = "user" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  account_type: AccountType;
  role: SecurityRole;
  created_at: string;
  has_tutor_profile: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}

export interface SignupData {
  full_name: string;
  email: string;
  password: string;
  account_type: AccountType;
}

export interface SessionInfo {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_used_at: string;
  expires_at: string;
  is_current: boolean;
}

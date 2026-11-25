import type { User } from "../types/auth";

// Where a user lands after login. The security role decides first (admins go
// to the admin dashboard); otherwise the account type picks the dashboard.
export function dashboardPath(user: Pick<User, "role" | "account_type">): string {
  if (user.role === "admin") {
    return "/admin";
  }
  return user.account_type === "tutor" ? "/dashboard/tutor" : "/dashboard/student";
}

// The personal (non-admin) dashboard of any user, admins included.
export function personalDashboardPath(user: Pick<User, "account_type">): string {
  return user.account_type === "tutor" ? "/dashboard/tutor" : "/dashboard/student";
}

// Only internal paths are accepted as a "next" redirect (no open redirects).
export function safeNextPath(next: string | null): string | null {
  if (next === null || !next.startsWith("/") || next.startsWith("//")) {
    return null;
  }
  return next;
}

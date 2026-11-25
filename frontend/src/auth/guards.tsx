// Route guards. They only improve usability (hiding pages a user cannot use);
// the backend still checks every request.
import type { ReactNode } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { AccountType } from "../types/auth";
import { useAuth } from "./AuthContext";
import { dashboardPath } from "./dashboardPath";

// Signed-in users only. Guests are sent to /login and come back afterwards.
export function RequireAuth({ children }: { children?: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status !== "authenticated") {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return children ?? <Outlet />;
}

// Administrators only.
export function RequireAdmin({ children }: { children?: ReactNode }) {
  const { user } = useAuth();
  if (user === null) {
    return <Navigate to="/login" replace />;
  }
  if (user.role !== "admin") {
    return <Navigate to="/forbidden" replace />;
  }
  return children ?? <Outlet />;
}

// A specific account type (e.g. only tutors create tutor profiles).
export function RequireAccountType({ type, children }: { type: AccountType; children?: ReactNode }) {
  const { user } = useAuth();
  if (user === null) {
    return <Navigate to="/login" replace />;
  }
  if (user.account_type !== type) {
    return <Navigate to="/forbidden" replace />;
  }
  return children ?? <Outlet />;
}

// Login and signup pages: signed-in users go straight to their dashboard.
export function GuestOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user !== null) {
    return <Navigate to={dashboardPath(user)} replace />;
  }
  return children;
}

// "/dashboard" picks the right dashboard for the current user.
export function DashboardRedirect() {
  const { user } = useAuth();
  return <Navigate to={user === null ? "/login" : dashboardPath(user)} replace />;
}

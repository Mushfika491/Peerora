// Central authentication state for the whole app.
//
// status:
//   "restoring"     - on first load, while the refresh cookie is exchanged
//                     for an access token (nothing is rendered yet, so a
//                     signed-in user never sees guest pages flash by)
//   "authenticated" - user is known, access token is in memory
//   "guest"         - not signed in
//
// If the backend reports that the account is suspended (a 403 tagged
// "account_suspended"), the session is cleared and the user is sent to /login.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/Toast";
import {
  ApiError,
  isAccountSuspended,
  setAccessToken,
  setRefreshHandler,
  setSuspendedHandler,
} from "../services/apiClient";
import * as authService from "../services/authService";
import type { SignupData, TokenResponse, User } from "../types/auth";

export type AuthStatus = "restoring" | "authenticated" | "guest";

interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  login: (email: string, password: string) => Promise<User>;
  signup: (data: SignupData) => Promise<User>;
  logout: () => Promise<void>;
  setUser: (user: User) => void; // after a profile update
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("restoring");
  const [user, setUserState] = useState<User | null>(null);
  const navigate = useNavigate();
  const toast = useToast();
  // Kept in refs so the handlers registered once below always use the latest values.
  const navigateRef = useRef(navigate);
  const toastRef = useRef(toast);
  navigateRef.current = navigate;
  toastRef.current = toast;

  const applyTokens = useCallback((tokens: TokenResponse): User => {
    setAccessToken(tokens.access_token);
    setUserState(tokens.user);
    setStatus("authenticated");
    return tokens.user;
  }, []);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUserState(null);
    setStatus("guest");
  }, []);

  // A banned account: forget the session, explain why, and go to the login page.
  const handleSuspended = useCallback(
    (message: string) => {
      clearSession();
      toastRef.current.error(message);
      navigateRef.current("/login", { replace: true });
    },
    [clearSession]
  );

  // Called by apiClient when a request gets 401 (access token expired).
  const refreshSession = useCallback(async (): Promise<string | null> => {
    try {
      const tokens = await authService.refresh();
      applyTokens(tokens);
      return tokens.access_token;
    } catch (error) {
      if (isAccountSuspended(error)) {
        handleSuspended((error as ApiError).message);
      } else if (error instanceof ApiError) {
        clearSession(); // 401: the session is over
      }
      return null; // (a network error leaves the state unchanged)
    }
  }, [applyTokens, clearSession, handleSuspended]);

  useEffect(() => {
    setRefreshHandler(refreshSession);
    setSuspendedHandler(handleSuspended);
    // Restore the session after a page reload. authService.refresh shares one
    // request between callers, so React StrictMode's double effect is safe.
    let active = true;
    authService
      .refresh()
      .then((tokens) => {
        if (active) {
          applyTokens(tokens);
        }
      })
      .catch(() => {
        if (active) {
          clearSession();
        }
      });
    return () => {
      active = false;
      setRefreshHandler(null);
      setSuspendedHandler(null);
    };
  }, [applyTokens, clearSession, refreshSession, handleSuspended]);

  const login = useCallback(
    async (email: string, password: string) => applyTokens(await authService.login(email, password)),
    [applyTokens]
  );

  const signup = useCallback(
    async (data: SignupData) => applyTokens(await authService.signup(data)),
    [applyTokens]
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      login,
      signup,
      logout,
      setUser: setUserState,
      isAdmin: user?.role === "admin",
    }),
    [status, user, login, signup, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used inside <AuthProvider>.");
  }
  return context;
}

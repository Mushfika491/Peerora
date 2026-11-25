import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ToastProvider } from "../components/Toast";
import { ROUTER_FUTURE } from "../routerFuture";
import { ApiError, apiGet } from "../services/apiClient";
import { jsonResponse, makeUser, tokenResponse } from "../test/helpers";
import { LocationProbe } from "../test/render";
import { AuthProvider, useAuth } from "./AuthContext";

function Probe() {
  const { status, user } = useAuth();
  return <p>{status === "authenticated" ? `signed in as ${user?.email}` : status}</p>;
}

function Providers({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter initialEntries={["/dashboard"]} future={ROUTER_FUTURE}>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route path="/dashboard" element={children} />
            <Route path="/login" element={<><LocationProbe /><Probe /></>} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </MemoryRouter>
  );
}

function suspendedResponse(): Response {
  return new Response(JSON.stringify({ detail: "Your account has been suspended. Contact an administrator." }), {
    status: 403,
    headers: { "Content-Type": "application/json", "X-Error-Code": "account_suspended" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("AuthProvider", () => {
  it("restores the session from the refresh cookie on load", async () => {
    const fetchMock = vi.fn(async () => jsonResponse(200, tokenResponse(makeUser())));
    vi.stubGlobal("fetch", fetchMock);
    render(<Providers><Probe /></Providers>);

    expect(screen.getByText("restoring")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("signed in as student@example.com")).toBeInTheDocument());
    // StrictMode-style double calls share one refresh request (no token reuse).
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/auth/refresh");
    expect(new Headers(init.headers).get("X-Requested-With")).toBe("peerora");
  });

  it("becomes a guest when there is no valid session", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(401, { detail: "No active session." })));
    render(<Providers><Probe /></Providers>);
    await waitFor(() => expect(screen.getByText("guest")).toBeInTheDocument());
  });

  it("refreshes an expired access token once and retries the request", async () => {
    let refreshCount = 0;
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/auth/refresh") {
        refreshCount += 1;
        return jsonResponse(200, tokenResponse(makeUser(), `access-${refreshCount}`));
      }
      const auth = new Headers(init?.headers).get("Authorization");
      return auth === "Bearer access-2"
        ? jsonResponse(200, { ok: true })
        : jsonResponse(401, { detail: "Your session token is invalid or has expired." });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<Providers><Probe /></Providers>);
    await waitFor(() => expect(screen.getByText(/signed in/)).toBeInTheDocument());

    // access-1 is "expired": the client refreshes (access-2) and retries.
    await expect(apiGet("/api/users/me")).resolves.toEqual({ ok: true });
    expect(refreshCount).toBe(2);
  });

  it("signs a suspended user out and redirects to the login page", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) =>
      url === "/api/auth/refresh" ? jsonResponse(200, tokenResponse(makeUser())) : suspendedResponse()
    ));
    render(<Providers><Probe /></Providers>);
    await waitFor(() => expect(screen.getByText(/signed in/)).toBeInTheDocument());

    const error = await apiGet("/api/groups").catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("account_suspended");
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/login"));
    expect(screen.getByText("guest")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("suspended");
  });

  it("does NOT sign the user out for an ordinary permission error", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) =>
      url === "/api/auth/refresh"
        ? jsonResponse(200, tokenResponse(makeUser()))
        : jsonResponse(403, { detail: "You do not have permission to edit this record." })
    ));
    render(<Providers><Probe /></Providers>);
    await waitFor(() => expect(screen.getByText(/signed in/)).toBeInTheDocument());

    await expect(apiGet("/api/records/1")).rejects.toMatchObject({ status: 403, code: null });
    expect(screen.getByText("signed in as student@example.com")).toBeInTheDocument();
    expect(screen.queryByTestId("location")).not.toBeInTheDocument();
  });

  it("treats a suspended refresh as a sign-out", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => suspendedResponse()));
    render(<Providers><Probe /></Providers>);
    await waitFor(() => expect(screen.getByText("guest")).toBeInTheDocument());
  });
});

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { ROUTER_FUTURE } from "../routerFuture";
import { makeUser } from "../test/helpers";
import type { User } from "../types/auth";

// The guards read the user from AuthContext; replace it with a fixed value.
let mockUser: User | null = null;
vi.mock("./AuthContext", () => ({
  useAuth: () => ({ user: mockUser, status: mockUser === null ? "guest" : "authenticated" }),
}));

const { RequireAdmin, RequireAuth, RequireAccountType } = await import("./guards");

function renderAt(path: string, element: JSX.Element) {
  return render(
    <MemoryRouter initialEntries={[path]} future={ROUTER_FUTURE}>
      <Routes>
        <Route path="/protected" element={element} />
        <Route path="/login" element={<p>login page</p>} />
        <Route path="/forbidden" element={<p>forbidden page</p>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("route guards", () => {
  it("sends guests to the login page", () => {
    mockUser = null;
    renderAt("/protected", <RequireAuth><p>secret</p></RequireAuth>);
    expect(screen.getByText("login page")).toBeInTheDocument();
  });

  it("blocks non-admins from admin pages", () => {
    mockUser = makeUser({ role: "user" });
    renderAt("/protected", <RequireAdmin><p>admin area</p></RequireAdmin>);
    expect(screen.getByText("forbidden page")).toBeInTheDocument();
  });

  it("lets admins into admin pages", () => {
    mockUser = makeUser({ role: "admin" });
    renderAt("/protected", <RequireAdmin><p>admin area</p></RequireAdmin>);
    expect(screen.getByText("admin area")).toBeInTheDocument();
  });

  it("limits tutor-only pages to tutor accounts", () => {
    mockUser = makeUser({ account_type: "student" });
    renderAt("/protected", <RequireAccountType type="tutor"><p>tutor setup</p></RequireAccountType>);
    expect(screen.getByText("forbidden page")).toBeInTheDocument();
  });
});

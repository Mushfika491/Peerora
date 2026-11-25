// Admin restrictions in the UI (the backend enforces them too; see test_admin_users.py).
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { makeUser } from "../../test/helpers";
import { renderWithRouter } from "../../test/render";
import type { AdminUserDetail } from "../../types/admin";

const service = vi.hoisted(() => ({
  getUserDetail: vi.fn(),
  banUser: vi.fn(),
  unbanUser: vi.fn(),
  changeRole: vi.fn(),
  revokeUserSession: vi.fn(),
  revokeAllUserSessions: vi.fn(),
}));
vi.mock("../../services/adminService", () => service);

const auth = vi.hoisted(() => ({ user: null as unknown }));
vi.mock("../../auth/AuthContext", () => ({ useAuth: () => ({ user: auth.user }) }));

const { default: AdminUserDetailPage } = await import("./AdminUserDetailPage");

function detail(changes: Partial<AdminUserDetail["user"]>): AdminUserDetail {
  return {
    user: {
      id: 5, email: "sam@x.io", full_name: "Sam Student", account_type: "student", role: "user",
      is_banned: false, ban_reason: null, banned_at: null, last_login_at: null, created_at: "2026-11-20T10:00:00Z",
      ...changes,
    },
    tutor_profile_id: null, groups: [], records: [], record_count: 0, active_sessions: [], recent_activity: [],
  };
}

function renderPage(userId = 5) {
  return renderWithRouter(<AdminUserDetailPage />, { path: `/admin/users/${userId}`, pattern: "/admin/users/:id" });
}

beforeEach(() => {
  vi.clearAllMocks();
  auth.user = makeUser({ id: 1, role: "admin" });
});

describe("AdminUserDetailPage", () => {
  it("cannot ban another administrator", async () => {
    service.getUserDetail.mockResolvedValue(detail({ role: "admin" }));
    renderPage();
    expect(await screen.findByRole("button", { name: "Ban user" })).toBeDisabled();
  });

  it("cannot ban themself or change their own role", async () => {
    service.getUserDetail.mockResolvedValue(detail({ id: 1, role: "admin" }));
    renderPage(1);
    expect(await screen.findByRole("button", { name: "Ban user" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Change role to user" })).toBeDisabled();
    expect(screen.getByText("You cannot ban yourself or change your own role.")).toBeInTheDocument();
  });

  it("requires a reason to unban and sends it", async () => {
    service.getUserDetail.mockResolvedValue(detail({ is_banned: true, ban_reason: "Spam", banned_at: "2026-11-21T10:00:00Z" }));
    service.unbanUser.mockResolvedValue({});
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Unban user" }));
    const confirm = screen.getAllByRole("button", { name: "Unban user", hidden: true }).at(-1) as HTMLElement;
    fireEvent.click(confirm);
    expect(service.unbanUser).not.toHaveBeenCalled();
    expect(screen.getByText("Reason must be at least 3 characters.")).toBeInTheDocument();

    fireEvent.change(screen.getAllByLabelText(/Reason/).at(-1) as HTMLElement, { target: { value: "Appeal accepted" } });
    fireEvent.click(confirm);
    await waitFor(() => expect(service.unbanUser).toHaveBeenCalledWith(5, "Appeal accepted"));
  });
});

// The group page shows only the controls the member's permissions allow.
// (The backend enforces the same rules; see backend/tests/test_group_permissions.py.)
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { makeUser } from "../../test/helpers";
import { renderWithRouter } from "../../test/render";
import type { GroupMember, GroupPermissions, StudyGroup, StudyRecord } from "../../types/group";

const service = vi.hoisted(() => ({
  getGroup: vi.fn(),
  getMembers: vi.fn(),
  getGroupRecords: vi.fn(),
  updateMember: vi.fn(),
  addMember: vi.fn(),
  createGroupRecord: vi.fn(),
  removeMember: vi.fn(),
  updateGroup: vi.fn(),
  deleteGroup: vi.fn(),
  updateRecord: vi.fn(),
  deleteRecord: vi.fn(),
}));
vi.mock("../../services/groupService", () => service);

const auth = vi.hoisted(() => ({ user: null as unknown }));
vi.mock("../../auth/AuthContext", () => ({ useAuth: () => ({ user: auth.user }) }));

const { default: GroupDetailPage } = await import("./GroupDetailPage");

const NONE: GroupPermissions = { can_create_records: false, can_update_records: false, can_assign_records: false };
const ALL: GroupPermissions = { can_create_records: true, can_update_records: true, can_assign_records: true };

function group(role: StudyGroup["my_role"], permissions: GroupPermissions): StudyGroup {
  return {
    id: 1, name: "DBMS Group", description: null, subject: "DBMS", owner_id: 10, owner_name: "Olivia Owner",
    my_role: role, my_permissions: permissions, member_count: 2,
    created_at: "2026-11-20T10:00:00Z", updated_at: "2026-11-20T10:00:00Z",
  };
}

const members: GroupMember[] = [
  { user_id: 10, full_name: "Olivia Owner", email: "owner@x.io", group_role: "owner", ...ALL, joined_at: "2026-11-20T10:00:00Z" },
  { user_id: 20, full_name: "Mia Member", email: "mia@x.io", group_role: "member",
    can_create_records: true, can_update_records: false, can_assign_records: false, joined_at: "2026-11-21T10:00:00Z" },
];

const record: StudyRecord = {
  id: 5, title: "Normalize tables", content: null, status: "todo", due_date: null, group_id: 1, group_name: "DBMS Group",
  created_by_id: 10, created_by_name: "Olivia Owner", assigned_to_id: null, assigned_to_name: null,
  created_at: "2026-11-21T10:00:00Z", updated_at: "2026-11-21T10:00:00Z",
  can_edit: false, can_assign: false, can_delete: false,
};

function renderPage() {
  return renderWithRouter(<GroupDetailPage />, { path: "/groups/1", pattern: "/groups/:id" });
}

beforeEach(() => {
  vi.clearAllMocks();
  service.getMembers.mockResolvedValue(members);
  service.getGroupRecords.mockResolvedValue([record]);
});

describe("GroupDetailPage permissions", () => {
  it("read-only member: no create button, no settings, no member controls", async () => {
    auth.user = makeUser({ id: 30 });
    service.getGroup.mockResolvedValue(group("viewer", NONE));
    renderPage();
    expect(await screen.findByText("Normalize tables")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "New record" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Settings" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.getByText(/You can read everything in this group/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Members" }));
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Add member by email")).not.toBeInTheDocument();
  });

  it("create-only member can add records but cannot pick an assignee", async () => {
    auth.user = makeUser({ id: 20 });
    service.getGroup.mockResolvedValue(group("member", { ...NONE, can_create_records: true }));
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "New record" }));
    expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Assigned to")).not.toBeInTheDocument();
    expect(screen.getByText(/read everything and create records/)).toBeInTheDocument();
  });

  it("member with assign permission sees the assignee picker", async () => {
    auth.user = makeUser({ id: 20 });
    service.getGroup.mockResolvedValue(group("member", { ...NONE, can_create_records: true, can_assign_records: true }));
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "New record" }));
    expect(screen.getByLabelText("Assigned to")).toBeInTheDocument();
  });

  it("owner can toggle each member permission independently", async () => {
    auth.user = makeUser({ id: 10 });
    service.getGroup.mockResolvedValue(group("owner", ALL));
    service.updateMember.mockResolvedValue({ ...members[1], can_assign_records: true, group_role: "member" });
    renderPage();
    expect(await screen.findByRole("tab", { name: "Settings" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Members" }));

    const permissions = screen.getByRole("group", { name: "Permissions of Mia Member" });
    const create = within(permissions).getByRole("checkbox", { name: "Create" });
    const update = within(permissions).getByRole("checkbox", { name: "Update" });
    const assign = within(permissions).getByRole("checkbox", { name: "Assign" });
    expect([create, update, assign].map((box) => (box as HTMLInputElement).checked)).toEqual([true, false, false]);

    fireEvent.click(assign);
    await waitFor(() => expect(service.updateMember).toHaveBeenCalledWith(1, 20, { can_assign_records: true }));

    fireEvent.click(within(screen.getByText("Mia Member").closest("li") as HTMLElement).getByRole("button", { name: "None" }));
    await waitFor(() => expect(service.updateMember).toHaveBeenCalledWith(1, 20, { group_role: "viewer" }));
    // The owner's own row has no permission controls.
    expect(screen.queryByRole("group", { name: "Permissions of Olivia Owner" })).not.toBeInTheDocument();
  });
});

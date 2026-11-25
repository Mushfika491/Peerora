import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { GroupMember } from "../types/group";
import RecordForm from "./RecordForm";

const member: GroupMember = {
  user_id: 7, full_name: "Mia", email: "mia@x.io", group_role: "editor",
  can_create_records: true, can_update_records: true, can_assign_records: true, joined_at: "2026-11-20T10:00:00Z",
};

describe("RecordForm", () => {
  it("does not send an assignee when the user may not assign", () => {
    const onSubmit = vi.fn();
    render(<RecordForm isSubmitting={false} submitLabel="Save" onSubmit={onSubmit} onCancel={() => {}} />);
    fireEvent.change(screen.getByLabelText(/Title/), { target: { value: "Task" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty("assigned_to_id");
  });

  it("sends the chosen assignee when the picker is shown", () => {
    const onSubmit = vi.fn();
    render(<RecordForm members={[member]} isSubmitting={false} submitLabel="Save" onSubmit={onSubmit} onCancel={() => {}} />);
    fireEvent.change(screen.getByLabelText(/Title/), { target: { value: "Task" } });
    fireEvent.change(screen.getByLabelText("Assigned to"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ title: "Task", assigned_to_id: 7 });
  });

  it("requires a title", () => {
    const onSubmit = vi.fn();
    render(<RecordForm isSubmitting={false} submitLabel="Save" onSubmit={onSubmit} onCancel={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText("Title is required.")).toBeInTheDocument();
  });
});

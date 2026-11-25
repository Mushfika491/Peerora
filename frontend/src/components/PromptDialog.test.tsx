import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PromptDialog from "./PromptDialog";

function renderDialog(onConfirm = vi.fn()) {
  render(
    <PromptDialog isOpen title="Unban user?" message="They can log in again." inputLabel="Reason"
      required minLength={3} confirmLabel="Unban" onConfirm={onConfirm} onCancel={() => {}} />
  );
  return onConfirm;
}

describe("PromptDialog (reason input)", () => {
  it("refuses an empty or too-short reason", () => {
    const onConfirm = renderDialog();
    fireEvent.click(screen.getByRole("button", { name: "Unban", hidden: true }));
    expect(onConfirm).not.toHaveBeenCalled();
    expect(screen.getByText("Reason must be at least 3 characters.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: "  ok " } });
    fireEvent.click(screen.getByRole("button", { name: "Unban", hidden: true }));
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("passes a valid, trimmed reason", () => {
    const onConfirm = renderDialog();
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: "  Appeal accepted  " } });
    fireEvent.click(screen.getByRole("button", { name: "Unban", hidden: true }));
    expect(onConfirm).toHaveBeenCalledWith("Appeal accepted");
  });
});

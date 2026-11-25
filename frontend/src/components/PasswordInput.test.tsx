import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PasswordInput from "./PasswordInput";

function renderInForm(onSubmit = vi.fn((event: Event) => event.preventDefault())) {
  render(
    <form onSubmit={(event) => onSubmit(event.nativeEvent)}>
      <label htmlFor="pw">Password</label>
      <PasswordInput id="pw" defaultValue="Secret123" />
    </form>
  );
  return onSubmit;
}

describe("PasswordInput show/hide", () => {
  it("is hidden by default", () => {
    renderInForm();
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    const toggle = screen.getByRole("button", { name: "Show password" });
    expect(toggle).toHaveAttribute("aria-pressed", "false");
    expect(toggle).toHaveAttribute("aria-controls", "pw");
  });

  it("toggles between showing and hiding the password, keeping the value", () => {
    renderInForm();
    const input = screen.getByLabelText("Password");
    fireEvent.click(screen.getByRole("button", { name: "Show password" }));
    expect(input).toHaveAttribute("type", "text");
    expect(input).toHaveValue("Secret123");
    const hide = screen.getByRole("button", { name: "Hide password" });
    expect(hide).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(hide);
    expect(input).toHaveAttribute("type", "password");
  });

  it("is a keyboard-reachable button that never submits the form", () => {
    const onSubmit = renderInForm();
    const toggle = screen.getByRole("button", { name: "Show password" });
    expect(toggle.tagName).toBe("BUTTON");
    expect(toggle).toHaveAttribute("type", "button");
    expect(toggle).not.toHaveAttribute("tabindex", "-1");
    toggle.focus();
    expect(toggle).toHaveFocus();
    fireEvent.click(toggle);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("passes accessibility attributes through to the input", () => {
    render(<PasswordInput id="x" aria-invalid aria-describedby="x-error" autoComplete="new-password" />);
    const input = document.getElementById("x") as HTMLInputElement;
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", "x-error");
    expect(input).toHaveAttribute("autocomplete", "new-password");
  });
});

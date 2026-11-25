import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithRouter } from "../../test/render";

vi.mock("../../auth/AuthContext", () => ({ useAuth: () => ({ login: vi.fn() }) }));
const { default: LoginPage } = await import("./LoginPage");

describe("LoginPage", () => {
  it("shows a Forgot password? link and a hidden password with an eye toggle", () => {
    renderWithRouter(<LoginPage />, { path: "/login", pattern: "/login" });
    expect(screen.getByRole("link", { name: "Forgot password?" })).toHaveAttribute("href", "/forgot-password");
    const password = screen.getByLabelText(/^Password/);
    expect(password).toHaveAttribute("type", "password");
    fireEvent.click(screen.getByRole("button", { name: "Show password" }));
    expect(password).toHaveAttribute("type", "text");
  });
});

import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../services/apiClient";
import { renderWithRouter } from "../../test/render";

const service = vi.hoisted(() => ({ confirmPasswordReset: vi.fn() }));
vi.mock("../../services/authService", () => service);
const auth = vi.hoisted(() => ({ status: "guest", logout: vi.fn() }));
vi.mock("../../auth/AuthContext", () => ({ useAuth: () => auth }));
const { default: ResetPasswordPage, readResetToken } = await import("./ResetPasswordPage");

const TOKEN = "A".repeat(43);

function openLink(hash: string) {
  window.history.replaceState(null, "", `/reset-password${hash}`);
  return renderWithRouter(<ResetPasswordPage />, { path: "/reset-password", pattern: "/reset-password" });
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => window.history.replaceState(null, "", "/"));

describe("ResetPasswordPage", () => {
  it("reads only well-formed tokens from the URL fragment", () => {
    expect(readResetToken(`#token=${TOKEN}`)).toBe(TOKEN);
    expect(readResetToken("#token=short")).toBeNull();
    expect(readResetToken("#token=has spaces and !!")).toBeNull();
    expect(readResetToken("")).toBeNull();
  });

  it("removes the token from the address bar", () => {
    openLink(`#token=${TOKEN}`);
    expect(window.location.hash).toBe("");
    expect(screen.getByRole("button", { name: "Set new password" })).toBeInTheDocument();
  });

  it("explains an invalid link", () => {
    openLink("");
    expect(screen.getByRole("alert")).toHaveTextContent("invalid or incomplete");
    expect(screen.getByRole("link", { name: "Request a new link" })).toHaveAttribute("href", "/forgot-password");
  });

  it("checks the password policy and confirmation before sending", () => {
    openLink(`#token=${TOKEN}`);
    fireEvent.change(screen.getByLabelText(/^New password/), { target: { value: "short" } });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));
    expect(screen.getByText("Password must be at least 8 characters.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/^New password/), { target: { value: "NewPass456" } });
    fireEvent.change(screen.getByLabelText(/^Confirm new password/), { target: { value: "NewPass457" } });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));
    expect(screen.getByText("The passwords do not match.")).toBeInTheDocument();
    expect(service.confirmPasswordReset).not.toHaveBeenCalled();
  });

  it("resets the password and sends the user to the login page", async () => {
    service.confirmPasswordReset.mockResolvedValue("Your password has been reset. Please log in with your new password.");
    openLink(`#token=${TOKEN}`);
    fireEvent.change(screen.getByLabelText(/^New password/), { target: { value: "NewPass456" } });
    fireEvent.change(screen.getByLabelText(/^Confirm new password/), { target: { value: "NewPass456" } });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));
    await waitFor(() => expect(service.confirmPasswordReset).toHaveBeenCalledWith(TOKEN, "NewPass456"));
    expect(await screen.findByTestId("location")).toHaveTextContent("/login");
    expect(screen.getByRole("status")).toHaveTextContent("Your password has been reset");
  });

  it("shows the server's message for an expired or used link", async () => {
    service.confirmPasswordReset.mockRejectedValue(
      new ApiError("This password-reset link is invalid or has expired. Please request a new one.", 400)
    );
    openLink(`#token=${TOKEN}`);
    fireEvent.change(screen.getByLabelText(/^New password/), { target: { value: "NewPass456" } });
    fireEvent.change(screen.getByLabelText(/^Confirm new password/), { target: { value: "NewPass456" } });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("invalid or has expired");
  });
});

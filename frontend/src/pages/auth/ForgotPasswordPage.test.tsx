import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithRouter } from "../../test/render";

const service = vi.hoisted(() => ({
  getPasswordResetAvailability: vi.fn(),
  requestPasswordReset: vi.fn(),
}));
vi.mock("../../services/authService", () => service);
const { default: ForgotPasswordPage } = await import("./ForgotPasswordPage");

const GENERIC = "If an account exists for that email address, a password-reset link has been sent.";

beforeEach(() => vi.clearAllMocks());

describe("ForgotPasswordPage", () => {
  it("says honestly when email reset is not available", async () => {
    service.getPasswordResetAvailability.mockResolvedValue({ available: false, token_minutes: 30 });
    renderWithRouter(<ForgotPasswordPage />);
    expect(await screen.findByText(/not available on this server/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Send reset link" })).not.toBeInTheDocument();
  });

  it("shows the server's generic reply after a request", async () => {
    service.getPasswordResetAvailability.mockResolvedValue({ available: true, token_minutes: 30 });
    service.requestPasswordReset.mockResolvedValue(GENERIC);
    renderWithRouter(<ForgotPasswordPage />);
    fireEvent.change(await screen.findByLabelText(/Email/), { target: { value: " sam@example.com " } });
    fireEvent.click(screen.getByRole("button", { name: "Send reset link" }));
    await waitFor(() => expect(service.requestPasswordReset).toHaveBeenCalledWith("sam@example.com"));
    expect(await screen.findByText(GENERIC)).toBeInTheDocument();
  });

  it("validates the email before sending", async () => {
    service.getPasswordResetAvailability.mockResolvedValue({ available: true, token_minutes: 30 });
    renderWithRouter(<ForgotPasswordPage />);
    fireEvent.change(await screen.findByLabelText(/Email/), { target: { value: "not-an-email" } });
    fireEvent.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a valid email address.");
    expect(service.requestPasswordReset).not.toHaveBeenCalled();
  });
});

import { ApiError } from "../services/apiClient";

// Converts anything thrown by the service layer into a message for the user.
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "An unexpected error occurred. Please try again.";
}

// Pages can pass a message to the next page through the router's "state",
// e.g. navigate("/tutors", { state: { successMessage: "..." } }).
// The state is of unknown type, so it is checked before use.
export function getSuccessMessage(state: unknown): string | null {
  if (
    typeof state === "object" &&
    state !== null &&
    "successMessage" in state &&
    typeof state.successMessage === "string"
  ) {
    return state.successMessage;
  }
  return null;
}
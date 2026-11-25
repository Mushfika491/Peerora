// Mirrors the backend rules in backend/peerora/schemas/common.py. The backend
// remains the authority; these checks only give faster feedback.
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 128;

export function checkPassword(password: string, email = ""): string | undefined {
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`;
  }
  if (password.length > PASSWORD_MAX_LENGTH) {
    return `Password must be at most ${PASSWORD_MAX_LENGTH} characters.`;
  }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return "Password must contain at least one letter and one number.";
  }
  if (email !== "" && password.trim().toLowerCase() === email.trim().toLowerCase()) {
    return "Password must not be the same as your email address.";
  }
  return undefined;
}

export function checkEmail(email: string): string | undefined {
  const text = email.trim();
  if (text === "") {
    return "Email is required.";
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) {
    return "Enter a valid email address.";
  }
  return undefined;
}

export function checkFullName(name: string): string | undefined {
  const text = name.trim();
  if (text.length < 2) {
    return "Full name must be at least 2 characters.";
  }
  if (text.length > 100) {
    return "Full name must be at most 100 characters.";
  }
  return undefined;
}

// Step 1 of the password reset: ask for the account's email address.
// The reply is the same whether or not an account exists (no enumeration).
// If the server has no email service configured, the page says so honestly.
import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import ErrorState from "../../components/ErrorState";
import FormField from "../../components/FormField";
import LoadingState from "../../components/LoadingState";
import { useAsync } from "../../hooks/useAsync";
import { getPasswordResetAvailability, requestPasswordReset } from "../../services/authService";
import { checkEmail } from "../../utils/authValidation";
import { getErrorMessage } from "../../utils/messages";

function ForgotPasswordPage() {
  const availability = useAsync(getPasswordResetAvailability, []);
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sentMessage, setSentMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problem = checkEmail(email);
    if (problem !== undefined) {
      setError(problem);
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      setSentMessage(await requestPasswordReset(email.trim()));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  let content;
  if (availability.state.status === "loading") {
    content = <LoadingState message="Loading..." />;
  } else if (availability.state.status === "error") {
    content = <ErrorState message={availability.state.message} onRetry={availability.reload} />;
  } else if (!availability.state.data.available) {
    content = (
      <div className="alert alert-error" role="status">
        Password reset by email is not available on this server yet. Please contact an administrator
        to regain access to your account.
      </div>
    );
  } else if (sentMessage !== null) {
    content = (
      <>
        <div className="alert alert-success" role="status">{sentMessage}</div>
        <p className="muted small">
          Check your inbox (and spam folder). The link works once. You can request a new link if it expires.
        </p>
      </>
    );
  } else {
    content = (
      <>
        <p className="muted">
          Enter the email address of your Peerora account and we will send you a link to choose a new password.
        </p>
        {error !== null && <div className="alert alert-error" role="alert">{error}</div>}
        <form onSubmit={handleSubmit} noValidate>
          <fieldset className="form-fieldset" disabled={isSubmitting}>
            <FormField id="reset-email" label="Email" required>
              {(control) => (
                <input {...control} type="email" className="form-input" autoComplete="email"
                  value={email} onChange={(event) => setEmail(event.target.value)} />
              )}
            </FormField>
            <button type="submit" className="btn btn-primary btn-block">
              {isSubmitting ? "Sending..." : "Send reset link"}
            </button>
          </fieldset>
        </form>
      </>
    );
  }

  return (
    <main className="auth-panel">
      <div className="auth-card card">
        <h1>Forgot your password?</h1>
        {content}
        <p className="auth-switch muted">
          Remembered it? <Link to="/login">Back to login</Link>
        </p>
      </div>
    </main>
  );
}

export default ForgotPasswordPage;

// Step 2 of the password reset: the page the emailed link opens.
// The token is in the URL fragment (#token=...), which browsers never send to
// a server. It is read once and then removed from the address bar and history.
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import FormField from "../../components/FormField";
import PasswordInput from "../../components/PasswordInput";
import { useToast } from "../../components/Toast";
import { confirmPasswordReset } from "../../services/authService";
import { checkPassword } from "../../utils/authValidation";
import { getErrorMessage } from "../../utils/messages";

export function readResetToken(hash: string): string | null {
  const token = new URLSearchParams(hash.replace(/^#/, "")).get("token");
  return token !== null && /^[A-Za-z0-9_-]{20,200}$/.test(token) ? token : null;
}

function ResetPasswordPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { status, logout } = useAuth();
  const [token] = useState<string | null>(() => readResetToken(window.location.hash));
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<{ password?: string; confirm?: string }>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Remove the token from the address bar so it is not kept in history or shared by accident.
  useEffect(() => {
    if (window.location.hash !== "") {
      window.history.replaceState(window.history.state, "", window.location.pathname + window.location.search);
    }
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (token === null) {
      return;
    }
    const found = {
      password: checkPassword(password),
      confirm: password !== confirm ? "The passwords do not match." : undefined,
    };
    setErrors(found);
    if (found.password !== undefined || found.confirm !== undefined) {
      document.getElementById(found.password !== undefined ? "reset-password" : "reset-confirm")?.focus();
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const message = await confirmPasswordReset(token, password);
      if (status === "authenticated") {
        await logout(); // every session was ended by the reset, this one too
      }
      toast.success(message);
      navigate("/login", { replace: true });
    } catch (caught) {
      setSubmitError(getErrorMessage(caught));
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-panel">
      <div className="auth-card card">
        <h1>Choose a new password</h1>
        {token === null ? (
          <>
            <div className="alert alert-error" role="alert">
              This password-reset link is invalid or incomplete. Please request a new one.
            </div>
            <Link to="/forgot-password" className="btn btn-primary btn-block">Request a new link</Link>
          </>
        ) : (
          <>
            <p className="muted">After the change you will be signed out on every device.</p>
            {submitError !== null && (
              <div className="alert alert-error" role="alert">
                {submitError} <Link to="/forgot-password">Request a new link</Link>
              </div>
            )}
            <form onSubmit={handleSubmit} noValidate>
              <fieldset className="form-fieldset" disabled={isSubmitting}>
                <FormField id="reset-password" label="New password" required error={errors.password}
                  hint="At least 8 characters, with at least one letter and one number.">
                  {(control) => (
                    <PasswordInput {...control} autoComplete="new-password" value={password}
                      onChange={(event) => { setPassword(event.target.value); setErrors({}); }} />
                  )}
                </FormField>
                <FormField id="reset-confirm" label="Confirm new password" required error={errors.confirm}>
                  {(control) => (
                    <PasswordInput {...control} autoComplete="new-password" value={confirm}
                      onChange={(event) => { setConfirm(event.target.value); setErrors({}); }} />
                  )}
                </FormField>
                <button type="submit" className="btn btn-primary btn-block">
                  {isSubmitting ? "Saving..." : "Set new password"}
                </button>
              </fieldset>
            </form>
          </>
        )}
        <p className="auth-switch muted">
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </main>
  );
}

export default ResetPasswordPage;

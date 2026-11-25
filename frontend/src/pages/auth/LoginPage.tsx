import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { dashboardPath, safeNextPath } from "../../auth/dashboardPath";
import FormField from "../../components/FormField";
import PasswordInput from "../../components/PasswordInput";
import { useToast } from "../../components/Toast";
import { getErrorMessage } from "../../utils/messages";

function LoginPage() {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (email.trim() === "" || password === "") {
      setError("Enter your email and password.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const user = await login(email.trim(), password);
      toast.success(`Welcome back, ${user.full_name}.`);
      navigate(safeNextPath(searchParams.get("next")) ?? dashboardPath(user), { replace: true });
    } catch (caught) {
      setError(getErrorMessage(caught));
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <aside className="auth-aside">
        <h2>Welcome back to Peerora</h2>
        <p>Pick up where you left off.</p>
        <ul>
          <li>See tasks assigned to you</li>
          <li>Check your study groups</li>
          <li>Find a tutor for your next exam</li>
        </ul>
      </aside>
      <section className="auth-panel">
        <div className="auth-card card">
          <h1>Log in</h1>
          <p className="muted">Use the email and password of your Peerora account.</p>

          {error !== null && (
            <div className="alert alert-error" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <fieldset className="form-fieldset" disabled={isSubmitting}>
              <FormField id="login-email" label="Email" required>
                {(control) => (
                  <input
                    {...control}
                    type="email"
                    className="form-input"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                )}
              </FormField>
              <FormField
                id="login-password"
                label="Password"
                required
                labelAction={<Link to="/forgot-password">Forgot password?</Link>}
              >
                {(control) => (
                  <PasswordInput
                    {...control}
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                )}
              </FormField>
              <button type="submit" className="btn btn-primary btn-block">
                {isSubmitting ? "Logging in..." : "Log in"}
              </button>
            </fieldset>
          </form>
          <p className="auth-switch muted">
            New to Peerora? <Link to="/signup">Create an account</Link>
          </p>
        </div>
      </section>
    </main>
  );
}

export default LoginPage;

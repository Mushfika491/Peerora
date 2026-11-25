// Account settings: profile, password and active sessions.
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import ConfirmDialog from "../../components/ConfirmDialog";
import ErrorState from "../../components/ErrorState";
import FormField from "../../components/FormField";
import PasswordInput from "../../components/PasswordInput";
import LoadingState from "../../components/LoadingState";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import { changePassword, getSessions, revokeSession, updateProfile } from "../../services/userService";
import type { SessionInfo } from "../../types/auth";
import { checkEmail, checkFullName, checkPassword } from "../../utils/authValidation";
import { formatDateTime, describeUserAgent } from "../../utils/format";
import { getErrorMessage } from "../../utils/messages";

type Tab = "profile" | "password" | "sessions";

function ProfileTab() {
  const { user, setUser } = useAuth();
  const toast = useToast();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user === null) {
    return null;
  }
  const emailChanged = email.trim().toLowerCase() !== user.email;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problem = checkFullName(fullName) ?? checkEmail(email) ??
      (emailChanged && currentPassword === "" ? "Enter your current password to change your email." : undefined);
    if (problem !== undefined) {
      setError(problem);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const updated = await updateProfile({
        full_name: fullName.trim(),
        ...(emailChanged ? { email: email.trim(), current_password: currentPassword } : {}),
      });
      setUser(updated);
      setCurrentPassword("");
      toast.success("Profile updated.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate style={{ maxWidth: 640 }}>
      {error !== null && <div className="alert alert-error" role="alert">{error}</div>}
      <fieldset className="form-fieldset" disabled={busy}>
        <FormField id="profile-name" label="Full name" required>
          {(control) => (
            <input {...control} className="form-input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          )}
        </FormField>
        <FormField id="profile-email" label="Email" required>
          {(control) => (
            <input {...control} type="email" className="form-input" value={email} onChange={(e) => setEmail(e.target.value)} />
          )}
        </FormField>
        {emailChanged && (
          <FormField id="profile-current" label="Current password" required hint="Required to change your email.">
            {(control) => (
              <PasswordInput {...control} autoComplete="current-password"
                value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
            )}
          </FormField>
        )}
        <dl className="tutor-meta">
          <dt>Account type</dt>
          <dd><StatusBadge value={user.account_type} /></dd>
          <dt>Security role</dt>
          <dd><StatusBadge value={user.role} /></dd>
        </dl>
        <p className="muted small">The account type and role cannot be changed here.</p>
        <button type="submit" className="btn btn-primary">{busy ? "Saving..." : "Save profile"}</button>
      </fieldset>
    </form>
  );
}

function PasswordTab() {
  const { user } = useAuth();
  const toast = useToast();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problem = current === "" ? "Enter your current password." :
      checkPassword(next, user?.email) ?? (next !== confirm ? "The new passwords do not match." : undefined);
    if (problem !== undefined) {
      setError(problem);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await changePassword(current, next);
      setCurrent("");
      setNext("");
      setConfirm("");
      toast.success("Password changed. Your other devices were signed out.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate style={{ maxWidth: 640 }}>
      {error !== null && <div className="alert alert-error" role="alert">{error}</div>}
      <fieldset className="form-fieldset" disabled={busy}>
        <FormField id="pw-current" label="Current password" required>
          {(control) => (
            <PasswordInput {...control} autoComplete="current-password"
              value={current} onChange={(e) => setCurrent(e.target.value)} />
          )}
        </FormField>
        <FormField id="pw-new" label="New password" required hint="At least 8 characters, with a letter and a number.">
          {(control) => (
            <PasswordInput {...control} autoComplete="new-password"
              value={next} onChange={(e) => setNext(e.target.value)} />
          )}
        </FormField>
        <FormField id="pw-confirm" label="Confirm new password" required>
          {(control) => (
            <PasswordInput {...control} autoComplete="new-password"
              value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          )}
        </FormField>
        <button type="submit" className="btn btn-primary">{busy ? "Saving..." : "Change password"}</button>
      </fieldset>
    </form>
  );
}

function SessionsTab() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const { state, reload } = useAsync(getSessions, []);
  const [toRevoke, setToRevoke] = useState<SessionInfo | null>(null);
  const [busy, setBusy] = useState(false);

  async function confirmRevoke() {
    if (toRevoke === null) {
      return;
    }
    setBusy(true);
    try {
      await revokeSession(toRevoke.id);
      if (toRevoke.is_current) {
        await logout();
        navigate("/login", { replace: true });
        return;
      }
      toast.success("Session ended.");
      setToRevoke(null);
      reload();
    } catch (caught) {
      toast.error(getErrorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  if (state.status === "loading") {
    return <LoadingState message="Loading sessions..." />;
  }
  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={reload} />;
  }

  return (
    <div className="card">
      <p className="muted">Devices that are currently signed in to your account.</p>
      <ul className="item-list">
        {state.data.map((session) => (
          <li key={session.id} className="item">
            <div className="item-main">
              <p className="item-title">
                {describeUserAgent(session.user_agent)}{" "}
                {session.is_current && <span className="badge badge-success">This device</span>}
              </p>
              <p className="item-meta">
                <span>IP {session.ip_address ?? "unknown"}</span>
                <span>Signed in {formatDateTime(session.created_at)}</span>
                <span>Last active {formatDateTime(session.last_used_at)}</span>
              </p>
            </div>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setToRevoke(session)}>
              {session.is_current ? "Sign out here" : "Revoke"}
            </button>
          </li>
        ))}
      </ul>
      <ConfirmDialog
        isOpen={toRevoke !== null}
        title="End this session?"
        message={toRevoke?.is_current ? "You will be signed out on this device." : "That device will be signed out immediately."}
        confirmLabel="End session"
        isProcessing={busy}
        onConfirm={confirmRevoke}
        onCancel={() => setToRevoke(null)}
      />
    </div>
  );
}

function AccountPage() {
  const [tab, setTab] = useState<Tab>("profile");
  const tabs: { id: Tab; label: string }[] = [
    { id: "profile", label: "Profile" },
    { id: "password", label: "Password" },
    { id: "sessions", label: "Active sessions" },
  ];

  return (
    <>
      <div className="page-header">
        <h1>Account settings</h1>
      </div>
      <div className="tabs" role="tablist">
        {tabs.map((item) => (
          <button key={item.id} type="button" role="tab" className="tab"
            aria-selected={tab === item.id} onClick={() => setTab(item.id)}>
            {item.label}
          </button>
        ))}
      </div>
      {tab === "profile" && <ProfileTab />}
      {tab === "password" && <PasswordTab />}
      {tab === "sessions" && <SessionsTab />}
    </>
  );
}

export default AccountPage;

// One user, for administrators: details, groups, records, sessions, activity,
// ban/unban with a reason, role change and session revocation.
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import PromptDialog from "../../components/PromptDialog";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import {
  banUser,
  changeRole,
  getUserDetail,
  revokeAllUserSessions,
  revokeUserSession,
  unbanUser,
} from "../../services/adminService";
import { describeUserAgent, formatDateTime } from "../../utils/format";
import { getErrorMessage } from "../../utils/messages";

type Dialog = "ban" | "unban" | "role" | "revoke-all" | null;

function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const userId = Number(id);
  const { user: me } = useAuth();
  const toast = useToast();
  const { state, reload } = useAsync(() => getUserDetail(userId), [userId]);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<unknown>, message: string) {
    setBusy(true);
    try {
      await action();
      toast.success(message);
      setDialog(null);
      reload();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  if (state.status === "loading") {
    return <LoadingState message="Loading user..." />;
  }
  if (state.status === "error") {
    return state.httpStatus === 404 ? (
      <EmptyState title="User not found" message="This user does not exist." actionLabel="All users" actionTo="/admin/users" />
    ) : (
      <ErrorState message={state.message} onRetry={reload} />
    );
  }

  const detail = state.data;
  const target = detail.user;
  const isSelf = target.id === me?.id;
  const newRole = target.role === "admin" ? "user" : "admin";

  return (
    <>
      <Link to="/admin/users" className="back-link">&larr; All users</Link>
      <div className="page-header">
        <div>
          <h1>{target.full_name}</h1>
          <p className="muted" style={{ margin: 0 }}>{target.email} · User #{target.id}</p>
        </div>
        <div className="inline-actions">
          <StatusBadge value={target.account_type} />
          <StatusBadge value={target.role} />
          <StatusBadge value={target.is_banned ? "banned" : "active"} />
        </div>
      </div>

      {target.is_banned && (
        <div className="alert alert-error" role="status">
          Banned on {formatDateTime(target.banned_at)}. Reason: {target.ban_reason}
        </div>
      )}

      <section className="card">
        <h2 className="card-title">Actions</h2>
        {isSelf && <p className="muted small">You cannot ban yourself or change your own role.</p>}
        <div className="inline-actions">
          {target.is_banned ? (
            <button type="button" className="btn btn-secondary" disabled={isSelf} onClick={() => setDialog("unban")}>Unban user</button>
          ) : (
            <button type="button" className="btn btn-danger" disabled={isSelf || target.role === "admin"}
              title={target.role === "admin" ? "Administrators cannot be banned" : undefined}
              onClick={() => setDialog("ban")}>Ban user</button>
          )}
          <button type="button" className="btn btn-secondary" disabled={isSelf} onClick={() => setDialog("role")}>
            {newRole === "admin" ? "Promote to admin" : "Change role to user"}
          </button>
          <button type="button" className="btn btn-secondary" disabled={detail.active_sessions.length === 0}
            onClick={() => setDialog("revoke-all")}>Revoke all sessions</button>
          {detail.tutor_profile_id !== null && (
            <Link to={`/tutors/${detail.tutor_profile_id}`} className="btn btn-ghost">View tutor profile</Link>
          )}
        </div>
      </section>

      <div className="grid-2 section-gap">
        <section className="card">
          <h2 className="card-title">Account</h2>
          <dl className="tutor-meta">
            <dt>Joined</dt><dd>{formatDateTime(target.created_at)}</dd>
            <dt>Last login</dt><dd>{formatDateTime(target.last_login_at)}</dd>
            <dt>Records</dt><dd>{detail.record_count}</dd>
            <dt>Groups</dt><dd>{detail.groups.length}</dd>
          </dl>
          <h3 className="card-title">Groups</h3>
          {detail.groups.length === 0 ? <p className="muted small">Not a member of any group.</p> : (
            <ul className="item-list">
              {detail.groups.map((group) => (
                <li key={group.id} className="item">
                  <span>{group.name}</span>
                  <StatusBadge value={group.group_role} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2 className="card-title">Active sessions ({detail.active_sessions.length})</h2>
          {detail.active_sessions.length === 0 ? <p className="muted small">No active sessions.</p> : (
            <ul className="item-list">
              {detail.active_sessions.map((session) => (
                <li key={session.id} className="item">
                  <div className="item-main">
                    <p className="item-title">{describeUserAgent(session.user_agent)}</p>
                    <p className="item-meta">
                      <span>IP {session.ip_address ?? "unknown"}</span>
                      <span>Last active {formatDateTime(session.last_used_at)}</span>
                    </p>
                  </div>
                  <button type="button" className="btn btn-secondary btn-sm" disabled={busy}
                    onClick={() => run(() => revokeUserSession(target.id, session.id), "Session revoked.")}>
                    Revoke
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2 className="card-title">Records created ({detail.record_count})</h2>
          {detail.records.length === 0 ? <p className="muted small">No records.</p> : (
            <ul className="item-list">
              {detail.records.map((record) => (
                <li key={record.id} className="item">
                  <div className="item-main">
                    <p className="item-title">{record.title}</p>
                    <p className="item-meta"><span>{record.group_name ?? "Personal"}</span></p>
                  </div>
                  <StatusBadge value={record.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Recent activity</h2>
            <Link to={`/admin/audit?user_id=${target.id}`} className="btn btn-ghost btn-sm">Full log</Link>
          </div>
          {detail.recent_activity.length === 0 ? <p className="muted small">No activity recorded.</p> : (
            <ul className="item-list">
              {detail.recent_activity.map((log) => (
                <li key={log.id} className="item">
                  <div className="item-main">
                    <p className="item-title">{log.action.replace(/_/g, " ")}</p>
                    <p className="item-meta">
                      <span>{formatDateTime(log.created_at)}</span>
                      <span>IP {log.ip_address ?? "unknown"}</span>
                      {log.actor_email !== null && log.actor_id !== target.id && <span>by {log.actor_email}</span>}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <PromptDialog isOpen={dialog === "ban"} title={`Ban ${target.full_name}?`}
        message="The user is signed out everywhere and cannot log in until unbanned."
        inputLabel="Reason" required minLength={3} confirmLabel="Ban user" danger isProcessing={busy}
        onConfirm={(reason) => run(() => banUser(target.id, reason), "User banned.")}
        onCancel={() => setDialog(null)} />
      <PromptDialog isOpen={dialog === "unban"} title={`Unban ${target.full_name}?`}
        message="The user will be able to log in again. The reason is recorded in the activity log."
        inputLabel="Reason" required minLength={3} confirmLabel="Unban user"
        isProcessing={busy}
        onConfirm={(reason) => run(() => unbanUser(target.id, reason), "User unbanned.")}
        onCancel={() => setDialog(null)} />
      <ConfirmDialog isOpen={dialog === "role"} title="Change security role?"
        message={`${target.full_name} will become "${newRole}". ${newRole === "admin" ? "Administrators can manage every user and all content." : "They will lose all administrator access."}`}
        confirmLabel="Change role" isProcessing={busy}
        onConfirm={() => run(() => changeRole(target.id, newRole), `Role changed to ${newRole}.`)}
        onCancel={() => setDialog(null)} />
      <ConfirmDialog isOpen={dialog === "revoke-all"} title="Revoke all sessions?"
        message="The user will be signed out on every device." confirmLabel="Revoke all" isProcessing={busy}
        onConfirm={() => run(() => revokeAllUserSessions(target.id), "All sessions revoked.")}
        onCancel={() => setDialog(null)} />
    </>
  );
}

export default AdminUserDetailPage;

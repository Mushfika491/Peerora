// Security monitoring: failed login attempts grouped by IP address and by account.
import { useState } from "react";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import StatCard from "../../components/StatCard";
import { useAsync } from "../../hooks/useAsync";
import { getSecurityReport } from "../../services/adminService";
import type { FailedLoginGroup } from "../../types/admin";
import { describeUserAgent, formatDateTime, localTimeZoneName } from "../../utils/format";

function GroupTable({ title, label, rows }: { title: string; label: string; rows: FailedLoginGroup[] }) {
  return (
    <section className="card">
      <h2 className="card-title">{title}</h2>
      {rows.length === 0 ? <p className="empty-inline">No failed logins in this period.</p> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>{label}</th><th>Failures</th><th>Last attempt</th></tr></thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key}>
                  <td className="cell-wrap">{row.key}</td>
                  <td><strong>{row.failures}</strong></td>
                  <td className="small">{formatDateTime(row.last_attempt_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function AdminSecurityPage() {
  const [hours, setHours] = useState(24);
  const { state, reload } = useAsync(() => getSecurityReport(hours), [hours]);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Security monitoring</h1>
          <p className="muted small" style={{ margin: 0 }}>Times are shown in your timezone ({localTimeZoneName()}).</p>
        </div>
        <div className="inline-actions">
          <label htmlFor="security-hours" className="muted">Period</label>
          <select id="security-hours" className="form-input" style={{ width: "auto" }} value={hours}
            onChange={(e) => setHours(Number(e.target.value))}>
            <option value={1}>Last hour</option>
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
            <option value={720}>Last 30 days</option>
          </select>
          <button type="button" className="btn btn-secondary" onClick={reload}>Refresh</button>
        </div>
      </div>
      {state.status === "loading" && <LoadingState message="Loading security report..." />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={reload} />}
      {state.status === "success" && (
        <>
          <div className="stat-grid">
            <StatCard label="Failed logins" value={state.data.total_failures} tone="danger" />
            <StatCard label="Distinct IP addresses" value={state.data.by_ip.length} />
            <StatCard label="Distinct accounts" value={state.data.by_account.length} />
          </div>
          <div className="grid-2">
            <GroupTable title="By IP address" label="IP address" rows={state.data.by_ip} />
            <GroupTable title="By account" label="Email" rows={state.data.by_account} />
          </div>
          <section className="card section-gap">
            <h2 className="card-title">Most recent failures</h2>
            {state.data.recent.length === 0 ? <p className="empty-inline">No failed logins in this period.</p> : (
              <div className="table-wrap">
                <table className="table">
                  <thead><tr><th>Time</th><th>Email</th><th>Reason</th><th>IP address</th><th>Browser</th></tr></thead>
                  <tbody>
                    {state.data.recent.map((attempt, index) => (
                      <tr key={`${attempt.created_at}-${index}`}>
                        <td className="small">{formatDateTime(attempt.created_at)}</td>
                        <td className="cell-wrap">{attempt.email}</td>
                        <td>{(attempt.failure_reason ?? "").replace(/_/g, " ")}</td>
                        <td className="small">{attempt.ip_address ?? "—"}</td>
                        <td className="small">{describeUserAgent(attempt.user_agent)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}

export default AdminSecurityPage;

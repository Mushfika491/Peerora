import { Link } from "react-router-dom";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import StatCard from "../../components/StatCard";
import { useAsync } from "../../hooks/useAsync";
import { getOverview } from "../../services/adminService";

function AdminOverviewPage() {
  const { state, reload } = useAsync(getOverview, []);

  return (
    <>
      <div className="page-header">
        <div>
          <p className="eyebrow">Admin dashboard</p>
          <h1>Platform overview</h1>
        </div>
        <button type="button" className="btn btn-secondary" onClick={reload}>Refresh</button>
      </div>
      {state.status === "loading" && <LoadingState message="Loading statistics..." />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={reload} />}
      {state.status === "success" && (
        <div className="stat-grid">
          <StatCard label="Total users" value={state.data.total_users} />
          <StatCard label="Banned users" value={state.data.banned_users} tone="danger" />
          <StatCard label="New users (7 days)" value={state.data.new_users_last_7_days} tone="accent" />
          <StatCard label="Total records" value={state.data.total_records} />
          <StatCard label="Total groups" value={state.data.total_groups} />
          <StatCard label="Tutor profiles" value={state.data.total_tutor_profiles} />
          <StatCard label="Administrators" value={state.data.admin_users} />
        </div>
      )}
      <div className="grid-2">
        <section className="card">
          <h2 className="card-title">User management</h2>
          <p className="muted">Search users, review sessions and activity, ban or unban, and change roles.</p>
          <Link to="/admin/users" className="btn btn-primary">Manage users</Link>
        </section>
        <section className="card">
          <h2 className="card-title">Content moderation</h2>
          <p className="muted">Review and remove study records and study groups across the platform.</p>
          <Link to="/admin/content" className="btn btn-primary">Moderate content</Link>
        </section>
        <section className="card">
          <h2 className="card-title">Activity log</h2>
          <p className="muted">Logins, password changes, bans, role changes, deletions and exports.</p>
          <Link to="/admin/audit" className="btn btn-primary">Open activity log</Link>
        </section>
        <section className="card">
          <h2 className="card-title">Security monitoring</h2>
          <p className="muted">Failed login attempts by IP address and by account.</p>
          <Link to="/admin/security" className="btn btn-primary">View failed logins</Link>
        </section>
      </div>
    </>
  );
}

export default AdminOverviewPage;

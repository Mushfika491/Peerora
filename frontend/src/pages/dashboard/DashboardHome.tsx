// The personal dashboard. Students and tutors share the same building blocks;
// tutors also see the status of their tutor profile.
import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import RecordList from "../../components/RecordList";
import StatCard from "../../components/StatCard";
import StatusBadge from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";
import { getDashboardSummary } from "../../services/groupService";

function DashboardHome({ variant }: { variant: "student" | "tutor" }) {
  const { user } = useAuth();
  const { state, reload } = useAsync(getDashboardSummary, []);

  if (user === null) {
    return null;
  }
  if (state.status === "loading") {
    return <LoadingState message="Loading your dashboard..." />;
  }
  if (state.status === "error") {
    return <ErrorState title="Could not load your dashboard" message={state.message} onRetry={reload} />;
  }

  const summary = state.data;
  const firstName = user.full_name.split(" ")[0];

  return (
    <>
      <div className="page-header">
        <div>
          <p className="eyebrow">{variant === "tutor" ? "Tutor dashboard" : "Student dashboard"}</p>
          <h1>Welcome, {firstName}</h1>
        </div>
        <div className="inline-actions">
          <Link to="/groups?new=1" className="btn btn-secondary">New study group</Link>
          <Link to="/tutors" className="btn btn-primary">Find tutors</Link>
        </div>
      </div>

      {variant === "tutor" && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <div className="card-header">
            <h2 className="card-title">Your tutor profile</h2>
            {summary.tutor_profile_id !== null ? (
              <span className="badge badge-success">Published</span>
            ) : (
              <span className="badge badge-warning">Not created yet</span>
            )}
          </div>
          {summary.tutor_profile_id !== null ? (
            <div className="inline-actions">
              <Link to={`/tutors/${summary.tutor_profile_id}`} className="btn btn-secondary">View profile</Link>
              <Link to={`/tutors/${summary.tutor_profile_id}/edit`} className="btn btn-primary">Edit profile</Link>
            </div>
          ) : (
            <>
              <p className="muted">Students can only find you after you publish a tutor profile.</p>
              <Link to="/tutors/new" className="btn btn-primary">Set up tutor profile</Link>
            </>
          )}
        </div>
      )}

      <div className="stat-grid">
        <StatCard label="Study groups" value={summary.group_count} />
        <StatCard label="To do" value={summary.record_counts.todo} />
        <StatCard label="In progress" value={summary.record_counts.in_progress} tone="accent" />
        <StatCard label="Done" value={summary.record_counts.done} />
      </div>

      <div className="grid-2">
        <section className="card" aria-labelledby="assigned-heading">
          <div className="card-header">
            <h2 id="assigned-heading" className="card-title">Assigned to me</h2>
          </div>
          <RecordList
            records={summary.assigned_to_me}
            showGroup
            emptyText="Nothing is assigned to you right now."
            onChanged={reload}
          />
        </section>

        <section className="card" aria-labelledby="groups-heading">
          <div className="card-header">
            <h2 id="groups-heading" className="card-title">My study groups</h2>
            <Link to="/groups" className="btn btn-ghost btn-sm">View all</Link>
          </div>
          {summary.groups.length === 0 ? (
            <p className="empty-inline">
              You are not in any group yet. <Link to="/groups?new=1">Create one</Link>.
            </p>
          ) : (
            <ul className="item-list">
              {summary.groups.map((group) => (
                <li key={group.id} className="item">
                  <div className="item-main">
                    <Link to={`/groups/${group.id}`} className="item-title">{group.name}</Link>
                    <p className="item-meta">
                      <span>{group.member_count} members</span>
                      {group.subject !== null && <span>{group.subject}</span>}
                    </p>
                  </div>
                  <StatusBadge value={group.my_role} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card" aria-labelledby="personal-heading">
          <div className="card-header">
            <h2 id="personal-heading" className="card-title">My open personal records</h2>
            <Link to="/records" className="btn btn-ghost btn-sm">Manage</Link>
          </div>
          <RecordList
            records={summary.personal_open}
            emptyText="No open personal records."
            onChanged={reload}
          />
        </section>
      </div>
    </>
  );
}

export default DashboardHome;

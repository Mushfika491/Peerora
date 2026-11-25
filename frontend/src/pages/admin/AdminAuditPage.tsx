// Audit and activity log with search, filters, pagination and CSV export.
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import Pagination from "../../components/Pagination";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import { exportCsv, getAuditActions, listAuditLogs } from "../../services/adminService";
import { describeUserAgent, formatDateTime, localTimeZoneName } from "../../utils/format";
import { getErrorMessage } from "../../utils/messages";

const PAGE_SIZE = 25;

// "2026-11-20" (date input) -> start or end of that day in the viewer's own
// timezone, converted to a UTC ISO string for the API (which stores UTC).
function dayBoundary(day: string, end: boolean): string {
  return day === "" ? "" : new Date(`${day}T${end ? "23:59:59" : "00:00:00"}`).toISOString();
}

function AdminAuditPage() {
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const query = {
    q: params.get("q") ?? "",
    action: params.get("action") ?? "",
    user_id: params.get("user_id") ?? "",
    date_from: dayBoundary(params.get("from") ?? "", false),
    date_to: dayBoundary(params.get("to") ?? "", true),
    page: Number(params.get("page") ?? "1") || 1,
    page_size: PAGE_SIZE,
  };
  const [search, setSearch] = useState(query.q);
  const actions = useAsync(getAuditActions, []);
  const { state, reload } = useAsync(() => listAuditLogs(query), [params.toString()]);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value === "") next.delete(key);
    else next.set(key, value);
    if (key !== "page") next.delete("page");
    setParams(next);
  }

  async function handleExport() {
    try {
      await exportCsv("audit-logs", query);
      toast.success("Activity log exported.");
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Activity log</h1>
          <p className="muted small" style={{ margin: 0 }}>
            Times are shown in your timezone ({localTimeZoneName()}). CSV exports use UTC.
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={handleExport}>Export CSV</button>
      </div>

      <form className="filter-bar" onSubmit={(e) => { e.preventDefault(); setFilter("q", search.trim()); }}>
        <div className="form-field grow">
          <label htmlFor="audit-search">Search</label>
          <input id="audit-search" type="search" className="form-input" placeholder="Action, IP address or browser"
            value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="form-field">
          <label htmlFor="audit-action">Action</label>
          <select id="audit-action" className="form-input" value={query.action} onChange={(e) => setFilter("action", e.target.value)}>
            <option value="">All actions</option>
            {actions.state.status === "success" && actions.state.data.map((action) => (
              <option key={action} value={action}>{action.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="audit-user">User id</label>
          <input id="audit-user" type="number" min={1} className="form-input" value={query.user_id}
            onChange={(e) => setFilter("user_id", e.target.value)} />
        </div>
        <div className="form-field">
          <label htmlFor="audit-from">From</label>
          <input id="audit-from" type="date" className="form-input" value={params.get("from") ?? ""}
            onChange={(e) => setFilter("from", e.target.value)} />
        </div>
        <div className="form-field">
          <label htmlFor="audit-to">To</label>
          <input id="audit-to" type="date" className="form-input" value={params.get("to") ?? ""}
            onChange={(e) => setFilter("to", e.target.value)} />
        </div>
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      {state.status === "loading" && <LoadingState message="Loading activity..." />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={reload} />}
      {state.status === "success" && (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th><th>Action</th><th>Actor</th><th>Target</th><th>IP address</th><th>Browser</th><th>Details</th>
                </tr>
              </thead>
              <tbody>
                {state.data.items.length === 0 && (
                  <tr><td colSpan={7} className="empty-inline">No activity matches these filters.</td></tr>
                )}
                {state.data.items.map((log) => (
                  <tr key={log.id}>
                    <td className="small" style={{ whiteSpace: "nowrap" }}>{formatDateTime(log.created_at)}</td>
                    <td><span className="badge badge-neutral">{log.action.replace(/_/g, " ")}</span></td>
                    <td className="cell-wrap small">{log.actor_email ?? "—"}</td>
                    <td className="cell-wrap small">
                      {log.target_user_email ?? (log.target_type !== null ? `${log.target_type} ${log.target_id ?? ""}` : "—")}
                    </td>
                    <td className="small">{log.ip_address ?? "—"}</td>
                    <td className="small">{describeUserAgent(log.user_agent)}</td>
                    <td className="cell-wrap small">
                      {log.details === null ? "—" : (
                        <code>{Object.entries(log.details).map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`).join("; ")}</code>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={state.data.page} pageSize={state.data.page_size} total={state.data.total}
            onPageChange={(value) => setFilter("page", String(value))} />
        </>
      )}
    </>
  );
}

export default AdminAuditPage;

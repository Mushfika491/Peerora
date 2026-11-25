// Searchable, filterable, paginated user list with bulk ban/unban and CSV export.
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import Pagination from "../../components/Pagination";
import PromptDialog from "../../components/PromptDialog";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import { bulkBan, bulkUnban, exportCsv, listUsers } from "../../services/adminService";
import { formatDateTime } from "../../utils/format";
import { getErrorMessage } from "../../utils/messages";

const PAGE_SIZE = 20;

function AdminUsersPage() {
  const { user: me } = useAuth();
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const query = {
    q: params.get("q") ?? "",
    role: params.get("role") ?? "",
    account_type: params.get("account_type") ?? "",
    status: params.get("status") ?? "",
    page: Number(params.get("page") ?? "1") || 1,
    page_size: PAGE_SIZE,
  };
  const [search, setSearch] = useState(query.q);
  const { state, reload } = useAsync(() => listUsers(query), [params.toString()]);
  const [selected, setSelected] = useState<number[]>([]);
  const [dialog, setDialog] = useState<"ban" | "unban" | null>(null);
  const [busy, setBusy] = useState(false);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value === "") {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    if (key !== "page") {
      next.delete("page");
    }
    setParams(next);
    setSelected([]);
  }

  function toggle(id: number) {
    setSelected((items) => (items.includes(id) ? items.filter((item) => item !== id) : [...items, id]));
  }

  async function runBulk(reason: string) {
    setBusy(true);
    try {
      const result = dialog === "ban" ? await bulkBan(selected, reason) : await bulkUnban(selected, reason);
      const skipped = result.results.filter((item) => item.result !== "done").length;
      toast.success(
        `${result.done} user(s) ${dialog === "ban" ? "banned" : "unbanned"}` +
          (skipped > 0 ? `, ${skipped} skipped (administrators, yourself or no change needed).` : ".")
      );
      setDialog(null);
      setSelected([]);
      reload();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    try {
      await exportCsv("users", query);
      toast.success("Users exported.");
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  const items = state.status === "success" ? state.data.items : [];
  const allSelected = items.length > 0 && items.every((item) => selected.includes(item.id));

  return (
    <>
      <div className="page-header">
        <h1>Users</h1>
        <button type="button" className="btn btn-secondary" onClick={handleExport}>Export CSV</button>
      </div>

      <form className="filter-bar" onSubmit={(e) => { e.preventDefault(); setFilter("q", search.trim()); }}>
        <div className="form-field grow">
          <label htmlFor="user-search">Search</label>
          <input id="user-search" type="search" className="form-input" placeholder="Name or email"
            value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="form-field">
          <label htmlFor="user-role">Role</label>
          <select id="user-role" className="form-input" value={query.role} onChange={(e) => setFilter("role", e.target.value)}>
            <option value="">All roles</option>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="user-type">Account type</label>
          <select id="user-type" className="form-input" value={query.account_type}
            onChange={(e) => setFilter("account_type", e.target.value)}>
            <option value="">All types</option>
            <option value="student">Student</option>
            <option value="tutor">Tutor</option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="user-status">Status</label>
          <select id="user-status" className="form-input" value={query.status} onChange={(e) => setFilter("status", e.target.value)}>
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="banned">Banned</option>
          </select>
        </div>
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      {selected.length > 0 && (
        <div className="bulk-bar">
          {selected.length} selected
          <button type="button" className="btn btn-danger btn-sm" onClick={() => setDialog("ban")}>Ban selected</button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setDialog("unban")}>Unban selected</button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSelected([])}>Clear</button>
        </div>
      )}

      {state.status === "loading" && <LoadingState message="Loading users..." />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={reload} />}
      {state.status === "success" && (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th className="col-check">
                    <input type="checkbox" aria-label="Select all users on this page" checked={allSelected}
                      onChange={() => setSelected(allSelected ? [] : items.map((item) => item.id))} />
                  </th>
                  <th>User</th>
                  <th>Type</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Last login</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 && (
                  <tr><td colSpan={7} className="empty-inline">No users match these filters.</td></tr>
                )}
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <input type="checkbox" aria-label={`Select ${item.email}`} checked={selected.includes(item.id)}
                        disabled={item.id === me?.id} onChange={() => toggle(item.id)} />
                    </td>
                    <td className="cell-wrap">
                      <Link to={`/admin/users/${item.id}`}><strong>{item.full_name}</strong></Link>
                      <div className="muted small">{item.email}</div>
                    </td>
                    <td><StatusBadge value={item.account_type} /></td>
                    <td><StatusBadge value={item.role} /></td>
                    <td><StatusBadge value={item.is_banned ? "banned" : "active"} /></td>
                    <td className="small">{formatDateTime(item.created_at)}</td>
                    <td className="small">{formatDateTime(item.last_login_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={state.data.page} pageSize={state.data.page_size} total={state.data.total}
            onPageChange={(page) => setFilter("page", String(page))} />
        </>
      )}

      <PromptDialog
        isOpen={dialog !== null}
        title={dialog === "ban" ? `Ban ${selected.length} user(s)?` : `Unban ${selected.length} user(s)?`}
        message={dialog === "ban"
          ? "Banned users are signed out everywhere and cannot log in. Administrators are skipped."
          : "These users will be able to log in again."}
        inputLabel="Reason"
        required
        minLength={3}
        confirmLabel={dialog === "ban" ? "Ban users" : "Unban users"}
        danger={dialog === "ban"}
        isProcessing={busy}
        onConfirm={runBulk}
        onCancel={() => setDialog(null)}
      />
    </>
  );
}

export default AdminUsersPage;

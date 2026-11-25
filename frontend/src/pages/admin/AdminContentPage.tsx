// Content moderation: every study record and study group on the platform,
// searchable, with single and bulk delete (all recorded in the audit log).
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import ConfirmDialog from "../../components/ConfirmDialog";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import Pagination from "../../components/Pagination";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import { deleteGroups, deleteRecords, exportCsv, listGroups, listRecords } from "../../services/adminService";
import { formatDateTime } from "../../utils/format";
import { getErrorMessage } from "../../utils/messages";

const PAGE_SIZE = 20;
type Kind = "records" | "groups";

function AdminContentPage() {
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const kind: Kind = params.get("tab") === "groups" ? "groups" : "records";
  const query = {
    q: params.get("q") ?? "",
    status: kind === "records" ? params.get("status") ?? "" : "",
    scope: kind === "records" ? params.get("scope") ?? "" : "",
    page: Number(params.get("page") ?? "1") || 1,
    page_size: PAGE_SIZE,
  };
  const [search, setSearch] = useState(query.q);
  const records = useAsync(() => (kind === "records" ? listRecords(query) : Promise.resolve(null)), [params.toString()]);
  const groups = useAsync(() => (kind === "groups" ? listGroups(query) : Promise.resolve(null)), [params.toString()]);
  const [selected, setSelected] = useState<number[]>([]);
  const [toDelete, setToDelete] = useState<number[] | null>(null);
  const [busy, setBusy] = useState(false);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value === "") next.delete(key);
    else next.set(key, value);
    if (key !== "page") next.delete("page");
    if (key === "tab") {
      next.delete("status");
      next.delete("scope");
      next.delete("q");
      setSearch("");
    }
    setParams(next);
    setSelected([]);
  }

  async function confirmDelete() {
    if (toDelete === null) return;
    setBusy(true);
    try {
      const result = kind === "records" ? await deleteRecords(toDelete) : await deleteGroups(toDelete);
      toast.success(`${result.done} ${kind === "records" ? "record(s)" : "group(s)"} deleted.`);
      setToDelete(null);
      setSelected([]);
      if (kind === "records") records.reload();
      else groups.reload();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    try {
      await exportCsv("records", query);
      toast.success("Records exported.");
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  }

  const active = kind === "records" ? records.state : groups.state;
  const page = active.status === "success" ? active.data : null;
  const ids = page?.items.map((item) => item.id) ?? [];
  const allSelected = ids.length > 0 && ids.every((id) => selected.includes(id));
  const toggle = (id: number) =>
    setSelected((items) => (items.includes(id) ? items.filter((item) => item !== id) : [...items, id]));

  return (
    <>
      <div className="page-header">
        <h1>Content moderation</h1>
        {kind === "records" && (
          <button type="button" className="btn btn-secondary" onClick={handleExport}>Export records CSV</button>
        )}
      </div>

      <div className="tabs" role="tablist">
        <button type="button" role="tab" className="tab" aria-selected={kind === "records"}
          onClick={() => setFilter("tab", "")}>Study records</button>
        <button type="button" role="tab" className="tab" aria-selected={kind === "groups"}
          onClick={() => setFilter("tab", "groups")}>Study groups</button>
      </div>

      <form className="filter-bar" onSubmit={(e) => { e.preventDefault(); setFilter("q", search.trim()); }}>
        <div className="form-field grow">
          <label htmlFor="content-search">Search</label>
          <input id="content-search" type="search" className="form-input"
            placeholder={kind === "records" ? "Title or creator email" : "Group name or owner email"}
            value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {kind === "records" && (
          <>
            <div className="form-field">
              <label htmlFor="content-status">Status</label>
              <select id="content-status" className="form-input" value={query.status}
                onChange={(e) => setFilter("status", e.target.value)}>
                <option value="">All</option>
                <option value="todo">To do</option>
                <option value="in_progress">In progress</option>
                <option value="done">Done</option>
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="content-scope">Type</label>
              <select id="content-scope" className="form-input" value={query.scope}
                onChange={(e) => setFilter("scope", e.target.value)}>
                <option value="">All</option>
                <option value="personal">Personal</option>
                <option value="group">Group</option>
              </select>
            </div>
          </>
        )}
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      {selected.length > 0 && (
        <div className="bulk-bar">
          {selected.length} selected
          <button type="button" className="btn btn-danger btn-sm" onClick={() => setToDelete(selected)}>Delete selected</button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSelected([])}>Clear</button>
        </div>
      )}

      {active.status === "loading" && <LoadingState message="Loading content..." />}
      {active.status === "error" && (
        <ErrorState message={active.message} onRetry={kind === "records" ? records.reload : groups.reload} />
      )}
      {page !== null && (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th className="col-check">
                    <input type="checkbox" aria-label="Select all on this page" checked={allSelected}
                      onChange={() => setSelected(allSelected ? [] : ids)} />
                  </th>
                  {kind === "records" ? (
                    <><th>Title</th><th>Status</th><th>Group</th><th>Created by</th><th>Created</th></>
                  ) : (
                    <><th>Group</th><th>Owner</th><th>Members</th><th>Records</th><th>Created</th></>
                  )}
                  <th><span className="visually-hidden">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {page.items.length === 0 && (
                  <tr><td colSpan={7} className="empty-inline">Nothing matches these filters.</td></tr>
                )}
                {records.state.status === "success" && records.state.data !== null && kind === "records" &&
                  records.state.data.items.map((record) => (
                    <tr key={record.id}>
                      <td><input type="checkbox" aria-label={`Select ${record.title}`}
                        checked={selected.includes(record.id)} onChange={() => toggle(record.id)} /></td>
                      <td className="cell-wrap">{record.title}</td>
                      <td><StatusBadge value={record.status} /></td>
                      <td>{record.group_name ?? <span className="muted">Personal</span>}</td>
                      <td className="cell-wrap">
                        <Link to={`/admin/users/${record.created_by_id}`}>{record.created_by_name}</Link>
                        <div className="muted small">{record.created_by_email}</div>
                      </td>
                      <td className="small">{formatDateTime(record.created_at)}</td>
                      <td><button type="button" className="btn btn-danger btn-sm" onClick={() => setToDelete([record.id])}>Delete</button></td>
                    </tr>
                  ))}
                {groups.state.status === "success" && groups.state.data !== null && kind === "groups" &&
                  groups.state.data.items.map((group) => (
                    <tr key={group.id}>
                      <td><input type="checkbox" aria-label={`Select ${group.name}`}
                        checked={selected.includes(group.id)} onChange={() => toggle(group.id)} /></td>
                      <td className="cell-wrap"><strong>{group.name}</strong>
                        {group.subject !== null && <div className="muted small">{group.subject}</div>}</td>
                      <td className="cell-wrap">
                        <Link to={`/admin/users/${group.owner_id}`}>{group.owner_name}</Link>
                        <div className="muted small">{group.owner_email}</div>
                      </td>
                      <td>{group.member_count}</td>
                      <td>{group.record_count}</td>
                      <td className="small">{formatDateTime(group.created_at)}</td>
                      <td><button type="button" className="btn btn-danger btn-sm" onClick={() => setToDelete([group.id])}>Delete</button></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page.page} pageSize={page.page_size} total={page.total}
            onPageChange={(value) => setFilter("page", String(value))} />
        </>
      )}

      <ConfirmDialog
        isOpen={toDelete !== null}
        title={`Delete ${toDelete?.length ?? 0} ${kind === "records" ? "record(s)" : "group(s)"}?`}
        message={kind === "groups"
          ? "Deleting a group also deletes its records and memberships. This cannot be undone."
          : "The selected records will be permanently deleted."}
        confirmLabel="Delete"
        isProcessing={busy}
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </>
  );
}

export default AdminContentPage;

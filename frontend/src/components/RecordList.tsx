// A list of study records with the actions the current user is allowed to use.
// The flags (can_edit, can_delete) come from the backend, which also re-checks
// every change.
import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { deleteRecord, updateRecord } from "../services/groupService";
import type { GroupMember, RecordInput, RecordStatus, StudyRecord } from "../types/group";
import { formatDate } from "../utils/format";
import { getErrorMessage } from "../utils/messages";
import ConfirmDialog from "./ConfirmDialog";
import RecordForm, { STATUS_OPTIONS } from "./RecordForm";
import StatusBadge from "./StatusBadge";
import { useToast } from "./Toast";

interface RecordListProps {
  records: StudyRecord[];
  members?: GroupMember[];
  showGroup?: boolean;
  emptyText: string;
  onChanged: () => void;
}

function RecordList({ records, members, showGroup = false, emptyText, onChanged }: RecordListProps) {
  const { user } = useAuth();
  const toast = useToast();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [toDelete, setToDelete] = useState<StudyRecord | null>(null);

  if (records.length === 0) {
    return <p className="empty-inline">{emptyText}</p>;
  }

  async function save(record: StudyRecord, changes: Partial<RecordInput>) {
    setBusy(true);
    try {
      await updateRecord(record.id, changes);
      toast.success("Record updated.");
      setEditingId(null);
      onChanged();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function confirmDelete() {
    if (toDelete === null) {
      return;
    }
    setBusy(true);
    try {
      await deleteRecord(toDelete.id);
      toast.success("Record deleted.");
      setToDelete(null);
      onChanged();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <ul className="item-list">
        {records.map((record) => {
          const isAssignee = user !== null && record.assigned_to_id === user.id;
          const canChangeStatus = record.can_edit || isAssignee;

          if (editingId === record.id) {
            return (
              <li key={record.id} className="item" style={{ display: "block" }}>
                <RecordForm
                  initial={record}
                  members={record.group_id !== null && record.can_assign ? members : undefined}
                  isSubmitting={busy}
                  submitLabel="Save changes"
                  onSubmit={(data) => save(record, data)}
                  onCancel={() => setEditingId(null)}
                />
              </li>
            );
          }

          return (
            <li key={record.id} className="item">
              <div className="item-main">
                <p className="item-title">{record.title}</p>
                <p className="item-meta">
                  <StatusBadge value={record.status} />
                  {showGroup && record.group_name !== null && <span>Group: {record.group_name}</span>}
                  {record.assigned_to_name !== null && <span>Assigned to {record.assigned_to_name}</span>}
                  {record.due_date !== null && <span>Due {formatDate(record.due_date)}</span>}
                  <span>By {record.created_by_name}</span>
                </p>
                {record.content !== null && <p className="item-body small">{record.content}</p>}
              </div>
              <div className="inline-actions">
                {canChangeStatus && (
                  <label className="visually-hidden" htmlFor={`status-${record.id}`}>
                    Status of {record.title}
                  </label>
                )}
                {canChangeStatus && (
                  <select
                    id={`status-${record.id}`}
                    className="form-input"
                    style={{ width: "auto" }}
                    value={record.status}
                    disabled={busy}
                    onChange={(event) => save(record, { status: event.target.value as RecordStatus })}
                  >
                    {STATUS_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                )}
                {record.can_edit && (
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setEditingId(record.id)}>
                    Edit
                  </button>
                )}
                {record.can_delete && (
                  <button type="button" className="btn btn-danger btn-sm" onClick={() => setToDelete(record)}>
                    Delete
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      <ConfirmDialog
        isOpen={toDelete !== null}
        title="Delete record?"
        message={`"${toDelete?.title ?? ""}" will be permanently deleted.`}
        confirmLabel="Delete"
        isProcessing={busy}
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </>
  );
}

export default RecordList;

// "My study groups": the groups the user belongs to, and a form to create one.
import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import FormField from "../../components/FormField";
import LoadingState from "../../components/LoadingState";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import { createGroup, getMyGroups } from "../../services/groupService";
import type { GroupInput } from "../../types/group";
import { getErrorMessage } from "../../utils/messages";

export function GroupForm({
  initial,
  submitLabel,
  isSubmitting,
  onSubmit,
  onCancel,
}: {
  initial?: GroupInput;
  submitLabel: string;
  isSubmitting: boolean;
  onSubmit: (data: GroupInput) => void;
  onCancel?: () => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [subject, setSubject] = useState(initial?.subject ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [error, setError] = useState<string | undefined>(undefined);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = name.trim();
    if (text.length < 2 || text.length > 100) {
      setError("Group name must be 2 to 100 characters.");
      document.getElementById("group-name")?.focus();
      return;
    }
    onSubmit({
      name: text,
      subject: subject.trim() === "" ? null : subject.trim(),
      description: description.trim() === "" ? null : description.trim(),
    });
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      <fieldset className="form-fieldset" disabled={isSubmitting}>
        <div className="form-row">
          <FormField id="group-name" label="Group name" required error={error}>
            {(control) => (
              <input {...control} className="form-input" maxLength={100} value={name}
                onChange={(e) => { setName(e.target.value); setError(undefined); }} />
            )}
          </FormField>
          <FormField id="group-subject" label="Subject">
            {(control) => (
              <input {...control} className="form-input" maxLength={100} placeholder="e.g. Database Management Systems"
                value={subject} onChange={(e) => setSubject(e.target.value)} />
            )}
          </FormField>
        </div>
        <FormField id="group-description" label="Description" counter={`${description.length} / 1000`}>
          {(control) => (
            <textarea {...control} className="form-input" rows={3} maxLength={1000}
              value={description} onChange={(e) => setDescription(e.target.value)} />
          )}
        </FormField>
        <div className="form-actions">
          <button type="submit" className="btn btn-primary">{isSubmitting ? "Saving..." : submitLabel}</button>
          {onCancel !== undefined && (
            <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
          )}
        </div>
      </fieldset>
    </form>
  );
}

function GroupsPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const showForm = searchParams.get("new") === "1";
  const { state, reload } = useAsync(getMyGroups, []);
  const [busy, setBusy] = useState(false);

  async function handleCreate(data: GroupInput) {
    setBusy(true);
    try {
      const group = await createGroup(data);
      toast.success("Study group created. You are its owner.");
      navigate(`/groups/${group.id}`);
    } catch (error) {
      toast.error(getErrorMessage(error));
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Study groups</h1>
          <p className="page-intro" style={{ margin: 0 }}>Groups you own or have been added to.</p>
        </div>
        {!showForm && (
          <button type="button" className="btn btn-primary" onClick={() => setSearchParams({ new: "1" })}>
            Create group
          </button>
        )}
      </div>

      {showForm && (
        <div style={{ marginBottom: "1.5rem" }}>
          <GroupForm submitLabel="Create group" isSubmitting={busy} onSubmit={handleCreate}
            onCancel={() => setSearchParams({})} />
        </div>
      )}

      {state.status === "loading" && <LoadingState message="Loading groups..." />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={reload} />}
      {state.status === "success" && state.data.length === 0 && !showForm && (
        <EmptyState title="No study groups yet"
          message="Create a group and add classmates by email. Only members can see a group." />
      )}
      {state.status === "success" && state.data.length > 0 && (
        <div className="group-grid">
          {state.data.map((group) => (
            <Link key={group.id} to={`/groups/${group.id}`} className="group-card">
              <div className="inline-actions" style={{ justifyContent: "space-between" }}>
                <h3>{group.name}</h3>
                <StatusBadge value={group.my_role} />
              </div>
              {group.subject !== null && <span className="muted small">{group.subject}</span>}
              {group.description !== null && <p className="small" style={{ margin: 0 }}>{group.description}</p>}
              <span className="muted small">
                {group.member_count} members · Owner: {group.owner_name}
              </span>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}

export default GroupsPage;

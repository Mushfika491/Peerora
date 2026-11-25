// One study group: shared records, members and (for the owner) settings.
// Each control follows the member's permissions (create / update / assign),
// and the backend enforces the same rules on every request.
import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import FormField from "../../components/FormField";
import LoadingState from "../../components/LoadingState";
import RecordForm from "../../components/RecordForm";
import RecordList from "../../components/RecordList";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import {
  addMember,
  createGroupRecord,
  deleteGroup,
  getGroup,
  getGroupRecords,
  getMembers,
  removeMember,
  updateGroup,
  updateMember,
} from "../../services/groupService";
import type { MemberPreset } from "../../services/groupService";
import type {
  GroupInput,
  GroupMember,
  GroupPermission,
  GroupPermissions,
  RecordInput,
  StudyGroup,
} from "../../types/group";
import { formatDate } from "../../utils/format";
import { getErrorMessage } from "../../utils/messages";
import { GroupForm } from "./GroupsPage";

type Tab = "records" | "members" | "settings";

export const PERMISSION_LABELS: { key: GroupPermission; label: string; help: string }[] = [
  { key: "can_create_records", label: "Create", help: "Add shared records" },
  { key: "can_update_records", label: "Update", help: "Edit shared records" },
  { key: "can_assign_records", label: "Assign", help: "Choose who a record is assigned to" },
];

// A sentence describing what the current user may do in this group.
export function describeAccess(group: Pick<StudyGroup, "my_role" | "my_permissions">): string {
  if (group.my_role === "owner") {
    return "You own this group: you can do everything, including editing the group, managing members and their permissions, and deleting it.";
  }
  const allowed = PERMISSION_LABELS.filter((item) => group.my_permissions[item.key]).map((item) =>
    item.label.toLowerCase()
  );
  const base = allowed.length === 0
    ? "You can read everything in this group"
    : `You can read everything and ${allowed.join(", ")} records`;
  return `${base}. You can always update the status of records assigned to you.`;
}

function RecordsTab({ group, members }: { group: StudyGroup; members: GroupMember[] }) {
  const toast = useToast();
  const { state, reload } = useAsync(() => getGroupRecords(group.id), [group.id]);
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const canCreate = group.my_permissions.can_create_records;
  const canAssign = group.my_permissions.can_assign_records;

  async function handleCreate(data: RecordInput) {
    setBusy(true);
    try {
      await createGroupRecord(group.id, data);
      toast.success("Record added to the group.");
      setShowForm(false);
      reload();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2 className="card-title">Shared records</h2>
        {canCreate && !showForm && (
          <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>
            New record
          </button>
        )}
      </div>
      {showForm && (
        <div style={{ marginBottom: "1rem" }}>
          <RecordForm members={canAssign ? members : undefined} isSubmitting={busy} submitLabel="Add record"
            onSubmit={handleCreate} onCancel={() => setShowForm(false)} />
        </div>
      )}
      {state.status === "loading" && <LoadingState message="Loading records..." />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={reload} />}
      {state.status === "success" && (
        <RecordList records={state.data} members={members}
          emptyText={canCreate ? "No records yet. Add the first one." : "No records yet."}
          onChanged={reload} />
      )}
    </section>
  );
}

function MembersTab({
  group,
  members,
  onChanged,
}: {
  group: StudyGroup;
  members: GroupMember[];
  onChanged: () => void;
}) {
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const isOwner = group.my_role === "owner";
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<MemberPreset>("viewer");
  const [busy, setBusy] = useState(false);
  const [toRemove, setToRemove] = useState<GroupMember | null>(null);

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (email.trim() === "") {
      toast.error("Enter the email address of the person to add.");
      return;
    }
    setBusy(true);
    try {
      const member = await addMember(group.id, email.trim(), role);
      toast.success(`${member.full_name} was added as ${member.group_role}.`);
      setEmail("");
      onChanged();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function changePermissions(
    member: GroupMember,
    changes: { group_role?: MemberPreset } & Partial<GroupPermissions>
  ) {
    setBusy(true);
    try {
      const updated = await updateMember(group.id, member.user_id, changes);
      toast.success(`${updated.full_name}'s permissions were updated (${updated.group_role}).`);
      onChanged();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function confirmRemove() {
    if (toRemove === null) {
      return;
    }
    setBusy(true);
    const leaving = toRemove.user_id === user?.id;
    try {
      await removeMember(group.id, toRemove.user_id);
      setToRemove(null);
      if (leaving) {
        toast.success(`You left ${group.name}.`);
        navigate("/groups", { replace: true });
        return;
      }
      toast.success(`${toRemove.full_name} was removed.`);
      onChanged();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2 className="card-title">Members ({members.length})</h2>
      </div>

      {isOwner && (
        <form className="filter-bar" onSubmit={handleAdd} noValidate>
          <FormField id="member-email" label="Add member by email">
            {(control) => (
              <input {...control} type="email" className="form-input" value={email}
                placeholder="classmate@university.edu" onChange={(e) => setEmail(e.target.value)} />
            )}
          </FormField>
          <FormField id="member-role" label="Starting permissions">
            {(control) => (
              <select {...control} className="form-input" value={role}
                onChange={(e) => setRole(e.target.value === "editor" ? "editor" : "viewer")}>
                <option value="viewer">Viewer (read only)</option>
                <option value="editor">Editor (create, update and assign)</option>
              </select>
            )}
          </FormField>
          <button type="submit" className="btn btn-primary" disabled={busy}>Add member</button>
        </form>
      )}

      <ul className="item-list">
        {members.map((member) => {
          const isMe = member.user_id === user?.id;
          return (
            <li key={member.user_id} className="item">
              <div className="item-main">
                <p className="item-title">
                  {member.full_name} {isMe && <span className="muted small">(you)</span>}
                </p>
                <p className="item-meta">
                  <span>{member.email}</span>
                  <span>Joined {formatDate(member.joined_at)}</span>
                </p>
              </div>
              <div className="inline-actions">
                <StatusBadge value={member.group_role} />
                {isOwner && member.group_role !== "owner" ? (
                  <>
                    <fieldset className="permission-set" disabled={busy}>
                      <legend className="visually-hidden">Permissions of {member.full_name}</legend>
                      {PERMISSION_LABELS.map((item) => (
                        <label key={item.key} className="permission-toggle" title={item.help}>
                          <input
                            type="checkbox"
                            checked={member[item.key]}
                            onChange={(event) => changePermissions(member, { [item.key]: event.target.checked })}
                          />
                          {item.label}
                        </label>
                      ))}
                    </fieldset>
                    <button type="button" className="btn btn-ghost btn-sm" disabled={busy}
                      onClick={() => changePermissions(member, { group_role: "editor" })}>
                      All
                    </button>
                    <button type="button" className="btn btn-ghost btn-sm" disabled={busy}
                      onClick={() => changePermissions(member, { group_role: "viewer" })}>
                      None
                    </button>
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => setToRemove(member)}>
                      Remove
                    </button>
                  </>
                ) : (
                  member.group_role !== "owner" && (
                    <span className="muted small">
                      {PERMISSION_LABELS.filter((item) => member[item.key]).map((item) => item.label).join(", ") ||
                        "Read only"}
                    </span>
                  )
                )}
                {!isOwner && isMe && (
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setToRemove(member)}>
                    Leave group
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      <ConfirmDialog
        isOpen={toRemove !== null}
        title={toRemove?.user_id === user?.id ? "Leave this group?" : "Remove member?"}
        message={
          toRemove?.user_id === user?.id
            ? "You will lose access to this group's records."
            : `${toRemove?.full_name ?? ""} will lose access to this group. Records assigned to them become unassigned.`
        }
        confirmLabel={toRemove?.user_id === user?.id ? "Leave" : "Remove"}
        isProcessing={busy}
        onConfirm={confirmRemove}
        onCancel={() => setToRemove(null)}
      />
    </section>
  );
}

function SettingsTab({ group, onChanged }: { group: StudyGroup; onChanged: () => void }) {
  const toast = useToast();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function handleSave(data: GroupInput) {
    setBusy(true);
    try {
      await updateGroup(group.id, data);
      toast.success("Group updated.");
      onChanged();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    try {
      await deleteGroup(group.id);
      toast.success("Group deleted.");
      navigate("/groups", { replace: true });
    } catch (error) {
      toast.error(getErrorMessage(error));
      setBusy(false);
      setConfirmDelete(false);
    }
  }

  return (
    <>
      <GroupForm initial={{ name: group.name, subject: group.subject, description: group.description }}
        submitLabel="Save changes" isSubmitting={busy} onSubmit={handleSave} />
      <section className="card">
        <h2 className="card-title">Delete group</h2>
        <p className="muted">Deleting the group also deletes all of its records and memberships.</p>
        <button type="button" className="btn btn-danger" onClick={() => setConfirmDelete(true)}>
          Delete group
        </button>
      </section>
      <ConfirmDialog isOpen={confirmDelete} title="Delete this group?"
        message={`"${group.name}" and all of its records will be permanently deleted.`}
        confirmLabel="Delete group" isProcessing={busy}
        onConfirm={handleDelete} onCancel={() => setConfirmDelete(false)} />
    </>
  );
}

function GroupDetailPage() {
  const { id } = useParams<{ id: string }>();
  const groupId = Number(id);
  const [tab, setTab] = useState<Tab>("records");
  const { state, reload } = useAsync(
    async () => {
      const [group, members] = await Promise.all([getGroup(groupId), getMembers(groupId)]);
      return { group, members };
    },
    [groupId]
  );

  if (!Number.isInteger(groupId) || groupId < 1) {
    return <EmptyState title="Group not found" message="This address is not valid." actionLabel="My groups" actionTo="/groups" />;
  }
  if (state.status === "loading") {
    return <LoadingState message="Loading group..." />;
  }
  if (state.status === "error") {
    if (state.httpStatus === 404) {
      return (
        <EmptyState title="Group not found"
          message="This group does not exist, or you are not a member of it."
          actionLabel="My groups" actionTo="/groups" />
      );
    }
    return <ErrorState message={state.message} onRetry={reload} />;
  }

  const { group, members } = state.data;
  const tabs: { id: Tab; label: string }[] = [
    { id: "records", label: "Records" },
    { id: "members", label: "Members" },
  ];
  if (group.my_role === "owner") {
    tabs.push({ id: "settings", label: "Settings" });
  }

  return (
    <>
      <Link to="/groups" className="back-link">&larr; All my groups</Link>
      <div className="page-header">
        <div>
          <h1>{group.name}</h1>
          <p className="muted" style={{ margin: 0 }}>
            {group.subject ?? "General"} · Owner: {group.owner_name} · {group.member_count} members
          </p>
        </div>
        <StatusBadge value={group.my_role} />
      </div>
      {group.description !== null && <p>{group.description}</p>}
      <div className="alert" style={{ background: "var(--color-primary-soft)" }}>{describeAccess(group)}</div>

      <div className="tabs" role="tablist">
        {tabs.map((item) => (
          <button key={item.id} type="button" role="tab" className="tab"
            aria-selected={tab === item.id} onClick={() => setTab(item.id)}>
            {item.label}
          </button>
        ))}
      </div>
      {tab === "records" && <RecordsTab group={group} members={members} />}
      {tab === "members" && <MembersTab group={group} members={members} onChanged={reload} />}
      {tab === "settings" && group.my_role === "owner" && <SettingsTab group={group} onChanged={reload} />}
    </>
  );
}

export default GroupDetailPage;

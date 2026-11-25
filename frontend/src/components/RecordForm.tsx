// Create or edit a study record. In a group, the assignee can be any member.
import { useState } from "react";
import type { FormEvent } from "react";
import type { GroupMember, RecordInput, RecordStatus, StudyRecord } from "../types/group";
import FormField from "./FormField";

interface RecordFormProps {
  initial?: StudyRecord;
  // The assignee picker is shown only when members are given (a group record
  // the user may assign). Otherwise assigned_to_id is not sent at all.
  members?: GroupMember[];
  isSubmitting: boolean;
  submitLabel: string;
  onSubmit: (data: RecordInput) => void;
  onCancel: () => void;
}

export const STATUS_OPTIONS: { value: RecordStatus; label: string }[] = [
  { value: "todo", label: "To do" },
  { value: "in_progress", label: "In progress" },
  { value: "done", label: "Done" },
];

function RecordForm({ initial, members, isSubmitting, submitLabel, onSubmit, onCancel }: RecordFormProps) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [content, setContent] = useState(initial?.content ?? "");
  const [status, setStatus] = useState<RecordStatus>(initial?.status ?? "todo");
  const [dueDate, setDueDate] = useState(initial?.due_date ?? "");
  const [assignee, setAssignee] = useState(initial?.assigned_to_id ? String(initial.assigned_to_id) : "");
  const [error, setError] = useState<string | undefined>(undefined);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = title.trim();
    if (text === "") {
      setError("Title is required.");
      document.getElementById("record-title")?.focus();
      return;
    }
    if (text.length > 200) {
      setError("Title must be at most 200 characters.");
      return;
    }
    onSubmit({
      title: text,
      content: content.trim() === "" ? null : content.trim(),
      status,
      due_date: dueDate === "" ? null : dueDate,
      ...(members !== undefined ? { assigned_to_id: assignee === "" ? null : Number(assignee) } : {}),
    });
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      <fieldset className="form-fieldset" disabled={isSubmitting}>
        <FormField id="record-title" label="Title" required error={error}>
          {(control) => (
            <input
              {...control}
              className="form-input"
              maxLength={200}
              value={title}
              onChange={(event) => {
                setTitle(event.target.value);
                setError(undefined);
              }}
            />
          )}
        </FormField>
        <FormField id="record-content" label="Details" counter={`${content.length} / 2000`}>
          {(control) => (
            <textarea
              {...control}
              className="form-input"
              rows={3}
              maxLength={2000}
              value={content}
              onChange={(event) => setContent(event.target.value)}
            />
          )}
        </FormField>
        <div className="form-row">
          <FormField id="record-status" label="Status">
            {(control) => (
              <select
                {...control}
                className="form-input"
                value={status}
                onChange={(event) => setStatus(event.target.value as RecordStatus)}
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            )}
          </FormField>
          <FormField id="record-due" label="Due date">
            {(control) => (
              <input
                {...control}
                type="date"
                className="form-input"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
              />
            )}
          </FormField>
          {members !== undefined && (
            <FormField id="record-assignee" label="Assigned to">
              {(control) => (
                <select
                  {...control}
                  className="form-input"
                  value={assignee}
                  onChange={(event) => setAssignee(event.target.value)}
                >
                  <option value="">Nobody</option>
                  {members.map((member) => (
                    <option key={member.user_id} value={member.user_id}>
                      {member.full_name} ({member.group_role})
                    </option>
                  ))}
                </select>
              )}
            </FormField>
          )}
        </div>
        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            {isSubmitting ? "Saving..." : submitLabel}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </fieldset>
    </form>
  );
}

export default RecordForm;

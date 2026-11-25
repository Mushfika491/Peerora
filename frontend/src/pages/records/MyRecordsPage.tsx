// Personal records (private to the user) and group records assigned to them.
import { useState } from "react";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import RecordForm from "../../components/RecordForm";
import RecordList from "../../components/RecordList";
import { useToast } from "../../components/Toast";
import { useAsync } from "../../hooks/useAsync";
import { createPersonalRecord, getMyRecords } from "../../services/groupService";
import type { RecordInput } from "../../types/group";
import { getErrorMessage } from "../../utils/messages";

function MyRecordsPage() {
  const toast = useToast();
  const personal = useAsync(() => getMyRecords("personal"), []);
  const assigned = useAsync(() => getMyRecords("assigned"), []);
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleCreate(data: RecordInput) {
    setBusy(true);
    try {
      await createPersonalRecord(data);
      toast.success("Record created.");
      setShowForm(false);
      personal.reload();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>My records</h1>
          <p className="page-intro" style={{ margin: 0 }}>
            Personal records are private: only you can see them.
          </p>
        </div>
        {!showForm && (
          <button type="button" className="btn btn-primary" onClick={() => setShowForm(true)}>
            New personal record
          </button>
        )}
      </div>

      {showForm && (
        <div style={{ marginBottom: "1.5rem" }}>
          <RecordForm isSubmitting={busy} submitLabel="Create record"
            onSubmit={handleCreate} onCancel={() => setShowForm(false)} />
        </div>
      )}

      <div className="grid-2">
        <section className="card" aria-labelledby="personal-records">
          <h2 id="personal-records" className="card-title">Personal records</h2>
          {personal.state.status === "loading" && <LoadingState />}
          {personal.state.status === "error" && (
            <ErrorState message={personal.state.message} onRetry={personal.reload} />
          )}
          {personal.state.status === "success" && (
            <RecordList records={personal.state.data} emptyText="You have no personal records yet."
              onChanged={personal.reload} />
          )}
        </section>
        <section className="card" aria-labelledby="assigned-records">
          <h2 id="assigned-records" className="card-title">Assigned to me in groups</h2>
          {assigned.state.status === "loading" && <LoadingState />}
          {assigned.state.status === "error" && (
            <ErrorState message={assigned.state.message} onRetry={assigned.reload} />
          )}
          {assigned.state.status === "success" && (
            <RecordList records={assigned.state.data} showGroup
              emptyText="No group records are assigned to you." onChanged={assigned.reload} />
          )}
        </section>
      </div>
    </>
  );
}

export default MyRecordsPage;

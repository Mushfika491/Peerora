import EmptyState from "../components/EmptyState";

function ForbiddenPage() {
  return (
    <main className="container page">
      <EmptyState
        title="You do not have access to this page"
        message="Your account does not have permission to open this page."
        actionLabel="Go to my dashboard"
        actionTo="/dashboard"
      />
    </main>
  );
}

export default ForbiddenPage;

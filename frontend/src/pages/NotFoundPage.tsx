import EmptyState from "../components/EmptyState";

function NotFoundPage() {
  return (
    <main className="container page">
      <EmptyState
        title="Page not found"
        message="The page you are looking for does not exist."
        actionLabel="Go to the home page"
        actionTo="/"
      />
    </main>
  );
}

export default NotFoundPage;
import { Link } from "react-router-dom";

interface EmptyStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  actionTo?: string;
  // "h1" when the message is the whole page (e.g. a 404), so the page still has a main heading.
  headingLevel?: "h1" | "h2";
}

function EmptyState({ title, message, actionLabel, actionTo, headingLevel = "h2" }: EmptyStateProps) {
  const Heading = headingLevel;
  return (
    <div className="state">
      <Heading>{title}</Heading>
      <p>{message}</p>
      {actionLabel !== undefined && actionTo !== undefined && (
        <Link to={actionTo} className="btn btn-primary">
          {actionLabel}
        </Link>
      )}
    </div>
  );
}

export default EmptyState;
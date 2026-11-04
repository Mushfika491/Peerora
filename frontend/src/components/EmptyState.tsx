import { Link } from "react-router-dom";

interface EmptyStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  actionTo?: string;
}

function EmptyState({ title, message, actionLabel, actionTo }: EmptyStateProps) {
  return (
    <div className="state">
      <h2>{title}</h2>
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
interface ErrorStateProps {
  message: string;
  title?: string;
  onRetry?: () => void;
}

function ErrorState({
  message,
  title = "Something went wrong",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="state state-error" role="alert">
      <h2>{title}</h2>
      <p>{message}</p>
      {onRetry !== undefined && (
        <button type="button" className="btn btn-primary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export default ErrorState;
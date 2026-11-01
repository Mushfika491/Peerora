interface LoadingStateProps {
  message?: string;
}

function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div className="state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true"></div>
      <p>{message}</p>
    </div>
  );
}

export default LoadingState;
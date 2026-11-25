const TONES: Record<string, string> = {
  todo: "badge badge-neutral",
  in_progress: "badge badge-warning",
  done: "badge badge-success",
  owner: "badge",
  editor: "badge badge-accent",
  viewer: "badge badge-neutral",
  admin: "badge",
  user: "badge badge-neutral",
  banned: "badge badge-danger",
  active: "badge badge-success",
  student: "badge badge-neutral",
  tutor: "badge badge-accent",
};

const LABELS: Record<string, string> = {
  todo: "To do",
  in_progress: "In progress",
  done: "Done",
};

// A small coloured label for statuses and roles.
function StatusBadge({ value }: { value: string }) {
  const label = LABELS[value] ?? value.replace(/_/g, " ");
  return (
    <span className={TONES[value] ?? "badge badge-neutral"} style={{ textTransform: "capitalize" }}>
      {label}
    </span>
  );
}

export default StatusBadge;

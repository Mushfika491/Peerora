interface StatCardProps {
  label: string;
  value: number | string;
  tone?: "default" | "danger" | "accent";
}

function StatCard({ label, value, tone = "default" }: StatCardProps) {
  return (
    <div className={tone === "default" ? "stat-card" : `stat-card tone-${tone}`}>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
    </div>
  );
}

export default StatCard;

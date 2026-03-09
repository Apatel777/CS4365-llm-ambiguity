interface MetricCardProps {
  label: string;
  value: string;
  hint: string;
}

export function MetricCard({ label, value, hint }: MetricCardProps) {
  return (
    <article className="metric-card">
      <p>{label}</p>
      <h3>{value}</h3>
      <span>{hint}</span>
    </article>
  );
}


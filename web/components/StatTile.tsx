export function StatTile({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="card px-4 py-3.5">
      <div className="stat-label">{label}</div>
      <div className="stat-value mt-1" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </div>
  );
}

export function ScorePill({
  strokes,
  vsPar,
  color,
}: {
  strokes: number | null;
  vsPar: string;
  color: string;
}) {
  return (
    <span
      className="pill"
      style={{ background: `color-mix(in srgb, ${color} 18%, transparent)`, color }}
    >
      <strong className="tabular-nums">{strokes ?? "—"}</strong>
      <span className="opacity-80">({vsPar})</span>
    </span>
  );
}

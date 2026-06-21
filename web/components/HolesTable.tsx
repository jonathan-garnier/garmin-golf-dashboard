import { Hole, vsPar, vsParColor } from "@/lib/api";

export default function HolesTable({
  holes,
  selected,
  onSelect,
}: {
  holes: Hole[];
  selected: number | null;
  onSelect: (h: number | null) => void;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-panel2 text-left text-xs uppercase tracking-wide text-muted">
            <th className="px-3 py-2 font-medium">Hole</th>
            <th className="px-3 py-2 font-medium">Par</th>
            <th className="px-3 py-2 font-medium">Score</th>
            <th className="px-3 py-2 font-medium">+/–</th>
            <th className="px-3 py-2 font-medium">Fairway</th>
          </tr>
        </thead>
        <tbody>
          {holes.map((h) => {
            const active = selected === h.hole_number;
            return (
              <tr
                key={h.hole_number}
                onClick={() => onSelect(active ? null : h.hole_number)}
                className={`cursor-pointer border-t border-border transition ${
                  active ? "bg-accent/10" : "hover:bg-panel2/60"
                }`}
              >
                <td className="px-3 py-2 font-medium tabular-nums">{h.hole_number}</td>
                <td className="px-3 py-2 tabular-nums text-muted">{h.par ?? "—"}</td>
                <td className="px-3 py-2 tabular-nums">{h.strokes ?? "—"}</td>
                <td
                  className="px-3 py-2 font-medium tabular-nums"
                  style={{ color: vsParColor(h.vs_par) }}
                >
                  {vsPar(h.vs_par)}
                </td>
                <td className="px-3 py-2 text-muted">
                  {h.fairway_outcome
                    ? h.fairway_outcome.charAt(0) + h.fairway_outcome.slice(1).toLowerCase()
                    : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

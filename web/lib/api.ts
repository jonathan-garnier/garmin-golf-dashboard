// API client + shared types for the golf dashboard frontend.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface Round {
  scorecard_id: number;
  start_time: string;
  course_name: string | null;
  tee_box: string | null;
  player_handicap: number | null;
  holes_completed: number | null;
  round_par: number | null;
  strokes: number | null;
  distance_walked: number | null;
  course_lat: number | null;
  course_lon: number | null;
  fit_file: string | null;
  vs_par: number | null;
  fairways_total?: number;
  fairways_hit?: number;
}

export interface Hole {
  scorecard_id: number;
  hole_number: number;
  par: number | null;
  strokes: number | null;
  handicap_score: number | null;
  fairway_outcome: string | null;
  pin_lat: number | null;
  pin_lon: number | null;
  vs_par: number | null;
}

export interface Shot {
  shot_id: number;
  scorecard_id: number;
  hole_number: number;
  shot_order: number | null;
  shot_time: string | null;
  shot_type: string | null;
  club_id: number | null;
  meters: number | null;
  start_lat: number | null;
  start_lon: number | null;
  start_lie: string | null;
  end_lat: number | null;
  end_lon: number | null;
  end_lie: string | null;
  auto_shot_type: string | null;
  exclude_from_stats: number;
}

export interface TrackPoint {
  scorecard_id: number;
  t: string | null;
  lat: number | null;
  lon: number | null;
  altitude: number | null;
  heart_rate: number | null;
}

export interface RoundDetail {
  round: Round;
  holes: Hole[];
  shots: Shot[];
  track: TrackPoint[];
}

export interface Trends {
  summary: {
    rounds: number;
    avg_vs_par: number | null;
    best_vs_par: number | null;
    worst_vs_par: number | null;
  };
  timeline: {
    scorecard_id: number;
    date: string;
    course: string | null;
    strokes: number | null;
    round_par: number | null;
    vs_par: number;
  }[];
  scoring: { name: string; count: number }[];
  shot_distance: { type: string; avg_m: number; count: number }[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  rounds: () => get<Round[]>("/api/rounds"),
  round: (id: number | string) => get<RoundDetail>(`/api/rounds/${id}`),
  trends: () => get<Trends>("/api/trends"),
};

// ---- shared display helpers ----

export const LIE_COLORS: Record<string, string> = {
  TeeBox: "#ffffff",
  Fairway: "#34c759",
  Rough: "#9acd32",
  Green: "#7cfc00",
  Bunker: "#e8d18b",
  Sand: "#e8d18b",
  Water: "#3aa0ff",
  Recovery: "#ff9f0a",
  OutOfBounds: "#ff453a",
};
export const DEFAULT_LIE = "#cbd5e1";

export function lieColor(lie: string | null): string {
  return (lie && LIE_COLORS[lie]) || DEFAULT_LIE;
}

export function vsPar(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  if (n === 0) return "E";
  return n > 0 ? `+${n}` : `${n}`;
}

// color for a score relative to par
export function vsParColor(n: number | null | undefined): string {
  if (n === null || n === undefined) return "var(--color-muted)";
  if (n < 0) return "#34c759";
  if (n === 0) return "#2ea3ff";
  if (n <= 5) return "#e8b84b";
  return "#ff6b6b";
}

export function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

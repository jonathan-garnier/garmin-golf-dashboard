"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { api, Trends, vsPar } from "@/lib/api";
import { StatTile } from "@/components/StatTile";

const SCORE_COLORS: Record<string, string> = {
  "Eagle+": "#2ecc71",
  Birdie: "#34c759",
  Par: "#2ea3ff",
  Bogey: "#e8b84b",
  Double: "#ff9f0a",
  "Triple+": "#ff6b6b",
};

const AXIS = { stroke: "#8b949e", fontSize: 12 };
const GRID = "#232b36";

export default function TrendsPage() {
  const [t, setT] = useState<Trends | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.trends().then(setT).catch((e) => setError(String(e)));
  }, []);

  if (error)
    return (
      <div className="card border-red-500/40 bg-red-500/10 px-4 py-3 text-red-300">
        {error}
      </div>
    );
  if (!t) return <div className="text-muted">Loading…</div>;

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Trends</h1>
        <p className="mt-1 text-muted">Scoring and shot patterns across all rounds.</p>
      </header>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Rounds" value={t.summary.rounds} />
        <StatTile label="Avg vs par" value={vsPar(t.summary.avg_vs_par)} />
        <StatTile label="Best" value={vsPar(t.summary.best_vs_par)} accent="#34c759" />
        <StatTile label="Worst" value={vsPar(t.summary.worst_vs_par)} accent="#ff6b6b" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Score vs par over time">
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={t.timeline} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#34c759" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#34c759" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="date" tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} />
              <YAxis tick={AXIS} tickLine={false} axisLine={false} />
              <ReferenceLine y={0} stroke="#2ea3ff" strokeDasharray="4 4" />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v) => [vsPar(Number(v)), "vs par"] as [string, string]}
              />
              <Area
                type="monotone"
                dataKey="vs_par"
                stroke="#34c759"
                strokeWidth={2}
                fill="url(#g)"
                dot={{ r: 3, fill: "#34c759" }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Scoring breakdown (all holes)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={t.scoring} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="name" tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} />
              <YAxis tick={AXIS} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#ffffff10" }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {t.scoring.map((s) => (
                  <Cell key={s.name} fill={SCORE_COLORS[s.name] ?? "#8b949e"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Average shot distance by type" full>
          {t.shot_distance.length === 0 ? (
            <p className="py-10 text-center text-muted">No shot data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(180, t.shot_distance.length * 46)}>
              <BarChart
                data={t.shot_distance}
                layout="vertical"
                margin={{ top: 4, right: 24, left: 20, bottom: 4 }}
              >
                <CartesianGrid stroke={GRID} horizontal={false} />
                <XAxis type="number" tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }}
                  unit=" m" />
                <YAxis type="category" dataKey="type" tick={AXIS} tickLine={false}
                  axisLine={false} width={90} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: "#ffffff10" }}
                  formatter={(v) => [`${Number(v)} m`, "avg distance"] as [string, string]}
                />
                <Bar dataKey="avg_m" radius={[0, 6, 6, 0]} fill="#2ea3ff" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </div>
  );
}

const tooltipStyle = {
  background: "#161b22",
  border: "1px solid #232b36",
  borderRadius: 12,
  color: "#e6edf3",
};

function ChartCard({
  title,
  children,
  full,
}: {
  title: string;
  children: React.ReactNode;
  full?: boolean;
}) {
  return (
    <div className={`card px-5 py-4 ${full ? "lg:col-span-2" : ""}`}>
      <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
        {title}
      </h2>
      {children}
    </div>
  );
}

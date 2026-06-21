"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  api,
  RoundDetail,
  vsPar,
  vsParColor,
  fmtDate,
  LIE_COLORS,
} from "@/lib/api";
import { StatTile } from "@/components/StatTile";
import HolesTable from "@/components/HolesTable";

const ShotMap = dynamic(() => import("@/components/ShotMap"), {
  ssr: false,
  loading: () => (
    <div className="grid h-[520px] place-items-center rounded-xl bg-panel2 text-muted">
      Loading map…
    </div>
  ),
});

export default function RoundDetailClient({ id }: { id: string }) {
  const [data, setData] = useState<RoundDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedHole, setSelectedHole] = useState<number | null>(null);
  const [showTrack, setShowTrack] = useState(true);
  const [hideNoise, setHideNoise] = useState(true);

  useEffect(() => {
    api.round(id).then(setData).catch((e) => setError(String(e)));
  }, [id]);

  const shotCount = useMemo(
    () =>
      data
        ? data.shots.filter((s) => !(hideNoise && s.exclude_from_stats)).length
        : 0,
    [data, hideNoise]
  );

  if (error)
    return (
      <div className="card border-red-500/40 bg-red-500/10 px-4 py-3 text-red-300">
        {error}
      </div>
    );
  if (!data) return <div className="text-muted">Loading…</div>;

  const { round, holes, track } = data;
  const hasTrack = track.length > 0;

  return (
    <div>
      <Link href="/" className="text-sm text-muted transition hover:text-text">
        ← All rounds
      </Link>

      <header className="mt-3 mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            {round.course_name ?? "Round"}
          </h1>
          <p className="mt-1 text-muted">{fmtDate(round.start_time)}</p>
        </div>
      </header>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
        <StatTile
          label="Score"
          value={
            <span style={{ color: vsParColor(round.vs_par) }}>
              {round.strokes ?? "—"}{" "}
              <span className="text-base opacity-80">({vsPar(round.vs_par)})</span>
            </span>
          }
          sub={`Par ${round.round_par ?? "—"}`}
        />
        <StatTile label="Holes" value={round.holes_completed ?? "—"} />
        <StatTile
          label="Fairways"
          value={
            round.fairways_total
              ? `${round.fairways_hit}/${round.fairways_total}`
              : "—"
          }
        />
        <StatTile
          label="Distance"
          value={`${((round.distance_walked ?? 0) / 1000).toFixed(2)} km`}
        />
        <StatTile label="Handicap" value={round.player_handicap ?? "—"} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* map + controls */}
        <div className="card overflow-hidden p-3">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <button
              onClick={() => setSelectedHole(null)}
              className={`pill ${
                selectedHole == null ? "bg-accent/20 text-accent" : "bg-panel2 text-muted"
              }`}
            >
              All holes
            </button>
            {holes.map((h) => (
              <button
                key={h.hole_number}
                onClick={() => setSelectedHole(h.hole_number)}
                className={`grid h-8 w-8 place-items-center rounded-lg text-sm tabular-nums transition ${
                  selectedHole === h.hole_number
                    ? "bg-accent text-black font-semibold"
                    : "bg-panel2 text-muted hover:text-text"
                }`}
              >
                {h.hole_number}
              </button>
            ))}
          </div>

          <ShotMap
            data={data}
            selectedHole={selectedHole}
            showTrack={showTrack}
            hideNoise={hideNoise}
          />

          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-sm">
            <div className="flex flex-wrap items-center gap-4">
              <label className={`flex items-center gap-2 ${hasTrack ? "" : "opacity-40"}`}>
                <input
                  type="checkbox"
                  checked={showTrack && hasTrack}
                  disabled={!hasTrack}
                  onChange={(e) => setShowTrack(e.target.checked)}
                  className="accent-[var(--color-accent)]"
                />
                Walk path
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={hideNoise}
                  onChange={(e) => setHideNoise(e.target.checked)}
                  className="accent-[var(--color-accent)]"
                />
                Hide noisy shots
              </label>
              <span className="text-muted">{shotCount} shots</span>
            </div>
          </div>

          <Legend />
        </div>

        {/* holes table */}
        <div>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">
            Holes
          </h2>
          <HolesTable holes={holes} selected={selectedHole} onSelect={setSelectedHole} />
        </div>
      </div>
    </div>
  );
}

function Legend() {
  const items = ["TeeBox", "Fairway", "Rough", "Green", "Bunker", "Water", "Recovery"];
  return (
    <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-border pt-3 text-xs text-muted">
      <span>Colour = lie at shot start:</span>
      {items.map((k) => (
        <span key={k} className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: LIE_COLORS[k] }}
          />
          {k}
        </span>
      ))}
    </div>
  );
}

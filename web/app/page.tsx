"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Round, vsPar, vsParColor, fmtDate } from "@/lib/api";
import { ScorePill } from "@/components/StatTile";

export default function RoundsPage() {
  const [rounds, setRounds] = useState<Round[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.rounds().then(setRounds).catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Rounds</h1>
        <p className="mt-1 text-muted">Every golf round, mapped shot by shot.</p>
      </header>

      {error && (
        <div className="card border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          Couldn’t reach the API ({error}). Is the backend running on :8000?
        </div>
      )}

      {!rounds && !error && <SkeletonGrid />}

      {rounds && rounds.length === 0 && (
        <div className="card px-5 py-6 text-muted">
          No rounds loaded. Run <code className="text-text">python fetch_golf.py</code>{" "}
          then <code className="text-text">python parse.py</code>.
        </div>
      )}

      {rounds && rounds.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {rounds.map((r) => (
            <Link
              key={r.scorecard_id}
              href={`/rounds/${r.scorecard_id}`}
              className="card card-hover group block px-5 py-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium leading-tight">
                    {r.course_name ?? "Unknown course"}
                  </div>
                  <div className="mt-0.5 text-sm text-muted">{fmtDate(r.start_time)}</div>
                </div>
                <ScorePill
                  strokes={r.strokes}
                  vsPar={vsPar(r.vs_par)}
                  color={vsParColor(r.vs_par)}
                />
              </div>

              <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted">
                <span>{r.holes_completed ?? "?"} holes</span>
                <span>Par {r.round_par ?? "—"}</span>
                {r.tee_box && <span>{r.tee_box} tees</span>}
                {r.distance_walked ? (
                  <span>{(r.distance_walked / 1000).toFixed(1)} km</span>
                ) : null}
              </div>

              <div className="mt-3 text-sm font-medium text-accent opacity-0 transition group-hover:opacity-100">
                View round →
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="card h-32 animate-pulse bg-panel/40" />
      ))}
    </div>
  );
}

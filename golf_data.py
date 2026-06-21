"""Shared data-shaping logic for the dashboard.

Pure functions that take a DB connection and return JSON-serializable dicts.
Used by both the live API (api.py) and the static exporter (export_static.py)
so there is a single source of truth.
"""
from collections import Counter

import db


def vs_par(strokes, par):
    if strokes is None or par is None:
        return None
    return strokes - par


def _score_bucket(diff):
    if diff is None:
        return None
    if diff <= -2:
        return "Eagle+"
    return {-1: "Birdie", 0: "Par", 1: "Bogey", 2: "Double"}.get(diff, "Triple+")


def compute_rounds(conn):
    rows = db.list_rounds(conn)
    for r in rows:
        r["vs_par"] = vs_par(r.get("strokes"), r.get("round_par"))
    return rows


def compute_round_detail(conn, rid):
    rnd = db.get_round(conn, rid)
    if not rnd:
        return None
    holes = db.get_holes(conn, rid)
    shots = db.get_shots(conn, rid)
    track = db.get_track(conn, rid)

    rnd["vs_par"] = vs_par(rnd.get("strokes"), rnd.get("round_par"))
    fairways = [h for h in holes if h.get("fairway_outcome")]
    rnd["fairways_total"] = len(fairways)
    rnd["fairways_hit"] = sum(1 for h in fairways if h["fairway_outcome"] == "HIT")
    for h in holes:
        h["vs_par"] = vs_par(h.get("strokes"), h.get("par"))
    return {"round": rnd, "holes": holes, "shots": shots, "track": track}


def compute_trends(conn):
    rounds = db.list_rounds(conn)
    all_holes, all_shots = [], []
    for r in rounds:
        all_holes.extend(db.get_holes(conn, r["scorecard_id"]))
        all_shots.extend(db.get_shots(conn, r["scorecard_id"]))

    timeline = [{
        "scorecard_id": r["scorecard_id"],
        "date": (r.get("start_time") or "")[:10],
        "course": r.get("course_name"),
        "strokes": r.get("strokes"),
        "round_par": r.get("round_par"),
        "vs_par": vs_par(r.get("strokes"), r.get("round_par")),
    } for r in rounds]
    timeline = [t for t in timeline if t["vs_par"] is not None]
    timeline.sort(key=lambda t: t["date"])

    vs_pars = [t["vs_par"] for t in timeline]
    summary = {
        "rounds": len(rounds),
        "avg_vs_par": round(sum(vs_pars) / len(vs_pars), 1) if vs_pars else None,
        "best_vs_par": min(vs_pars) if vs_pars else None,
        "worst_vs_par": max(vs_pars) if vs_pars else None,
    }

    buckets = Counter()
    for h in all_holes:
        b = _score_bucket(vs_par(h.get("strokes"), h.get("par")))
        if b:
            buckets[b] += 1
    order = ["Eagle+", "Birdie", "Par", "Bogey", "Double", "Triple+"]
    scoring = [{"name": k, "count": buckets.get(k, 0)} for k in order]

    by_type = {}
    for s in all_shots:
        if s.get("exclude_from_stats"):
            continue
        t, m = s.get("shot_type"), s.get("meters")
        if t and m is not None:
            by_type.setdefault(t, []).append(m)
    shot_distance = [
        {"type": t, "avg_m": round(sum(v) / len(v), 1), "count": len(v)}
        for t, v in sorted(by_type.items(), key=lambda kv: -len(kv[1]))
    ]

    return {
        "summary": summary,
        "timeline": timeline,
        "scoring": scoring,
        "shot_distance": shot_distance,
    }

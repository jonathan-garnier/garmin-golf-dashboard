"""Normalize cached Garmin JSON (+ matched FIT tracks) into golf.db.

Reads garmin_out/scorecard_<id>.json and shots_<id>.json, applies coordinate
conversions, joins par from the course snapshot, matches a FIT walk-path, and
writes the rounds/holes/shots/track_points tables.

Usage:
    python parse.py                # load every cached round into golf.db
    python parse.py 360966133      # load just one scorecard id
"""
import glob
import json
import os
import sys

import db
from util import (semi_to_deg, microdeg_to_deg, epoch_ms_to_iso, hole_pars)
from fit_track import read_fit, match_fit_to_round

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "garmin_out")

# Par corrections for courses whose Garmin course map was outdated when the
# round was played (the scorecard is frozen to that stale snapshot). Keyed by
# courseGlobalId -> correct holePars string. Only affects par/round_par; shot
# GPS positions are unaffected (they're measured, not course-derived).
COURSE_PAR_OVERRIDES = {
    19704: "333333333",  # Cammeray Golf Club — 9-hole par-3 (map was stale: showed 443443443)
}


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_round(scorecard_id):
    """Return (round_dict, hole_rows, shot_rows, track_rows) for one scorecard."""
    detail = _load_json(os.path.join(OUT, f"scorecard_{scorecard_id}.json"))
    sd = detail["scorecardDetails"][0]
    sc = sd["scorecard"]
    snap = (detail.get("courseSnapshots") or [{}])[0]

    # Apply a par override if this course's Garmin map was stale when played.
    holepars_str = COURSE_PAR_OVERRIDES.get(sc.get("courseGlobalId")) or snap.get("holePars")
    pars = hole_pars(holepars_str)
    round_par = (sum(int(c) for c in holepars_str)
                 if holepars_str and holepars_str.isdigit()
                 else snap.get("roundPar"))

    # ---- round ----
    fit_path = match_fit_to_round(HERE, sc.get("unitId"), sc.get("startTime"))
    round_row = {
        "scorecard_id": scorecard_id,
        "start_time": sc.get("startTime"),
        "course_name": snap.get("name") or sc.get("courseName"),
        "course_global_id": sc.get("courseGlobalId"),
        "tee_box": sc.get("teeBox"),
        "player_handicap": sc.get("playerHandicap"),
        "holes_completed": sc.get("holesCompleted"),
        "round_par": round_par,
        "strokes": sc.get("strokes"),
        "distance_walked": sc.get("distanceWalked"),
        "course_lat": microdeg_to_deg(snap.get("lat")),
        "course_lon": microdeg_to_deg(snap.get("lon")),
        "fit_file": os.path.basename(fit_path) if fit_path else None,
    }

    # ---- holes ----
    hole_rows = []
    for h in sc.get("holes", []):
        n = h.get("number")
        hole_rows.append({
            "scorecard_id": scorecard_id,
            "hole_number": n,
            "par": pars.get(n),
            "strokes": h.get("strokes"),
            "handicap_score": h.get("handicapScore"),
            "fairway_outcome": h.get("fairwayShotOutcome"),
            "pin_lat": semi_to_deg(h.get("pinPositionLat")),
            "pin_lon": semi_to_deg(h.get("pinPositionLon")),
        })

    # ---- shots ----
    shot_rows = []
    try:
        shots_doc = _load_json(os.path.join(OUT, f"shots_{scorecard_id}.json"))
    except FileNotFoundError:
        shots_doc = {"holeShots": []}
    for hs in shots_doc.get("holeShots", []):
        for s in hs.get("shots", []):
            start = s.get("startLoc") or {}
            end = s.get("endLoc") or {}
            shot_rows.append({
                "shot_id": s.get("id"),
                "scorecard_id": scorecard_id,
                "hole_number": s.get("holeNumber") or hs.get("holeNumber"),
                "shot_order": s.get("shotOrder"),
                "shot_time": epoch_ms_to_iso(s.get("shotTime")),
                "shot_type": s.get("shotType"),
                "club_id": s.get("clubId"),
                "meters": s.get("meters"),
                "start_lat": semi_to_deg(start.get("lat")),
                "start_lon": semi_to_deg(start.get("lon")),
                "start_lie": start.get("lie"),
                "end_lat": semi_to_deg(end.get("lat")),
                "end_lon": semi_to_deg(end.get("lon")),
                "end_lie": end.get("lie"),
                "auto_shot_type": s.get("autoShotType"),
                "exclude_from_stats": 1 if s.get("excludeFromStats") else 0,
            })

    # ---- track (optional FIT walk path) ----
    track_rows = []
    if fit_path:
        try:
            fit = read_fit(fit_path)
            for p in fit["track"]:
                track_rows.append({"scorecard_id": scorecard_id, **p})
        except Exception as e:
            print(f"  warn: FIT parse failed for {fit_path}: {e}")

    return round_row, hole_rows, shot_rows, track_rows


def load_round(conn, scorecard_id):
    round_row, holes, shots, track = parse_round(scorecard_id)
    db.clear_round(conn, scorecard_id)
    db.upsert_round(conn, round_row)
    db.insert_rows(conn, "holes", holes)
    db.insert_rows(conn, "shots", shots)
    db.insert_rows(conn, "track_points", track)
    conn.commit()
    print(f"  loaded id={scorecard_id}: {round_row['course_name']} "
          f"holes={len(holes)} shots={len(shots)} track={len(track)} "
          f"fit={round_row['fit_file']}")


def discover_ids():
    ids = []
    for p in glob.glob(os.path.join(OUT, "scorecard_*.json")):
        base = os.path.basename(p)
        try:
            ids.append(int(base[len("scorecard_"):-len(".json")]))
        except ValueError:
            pass
    return sorted(ids)


def main():
    conn = db.connect()
    db.init_schema(conn)
    ids = [int(sys.argv[1])] if len(sys.argv) > 1 else discover_ids()
    if not ids:
        print("No cached scorecards in garmin_out/. Run fetch_golf.py first.")
        return
    print(f"Loading {len(ids)} round(s) into {db.DB_PATH}:")
    for sid in ids:
        try:
            load_round(conn, sid)
        except Exception as e:
            print(f"  ERROR id={sid}: {type(e).__name__}: {e}")
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()

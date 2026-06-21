"""Export golf.db into static JSON files for the hosted (GitHub Pages) build.

Writes the same shapes the live API returns, into web/public/data/ so the
Next.js static export can bundle them — no server needed in production.

Run (after parse.py):
    python export_static.py

Output:
    web/public/data/rounds.json          (list)
    web/public/data/round-<id>.json      (per round)
    web/public/data/trends.json
"""
import json
import os

import db
import golf_data

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "web", "public", "data")


def _write(name, obj):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"), default=str)
    return path


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = db.connect()
    try:
        rounds = golf_data.compute_rounds(conn)
        _write("rounds.json", rounds)
        for r in rounds:
            rid = r["scorecard_id"]
            _write(f"round-{rid}.json", golf_data.compute_round_detail(conn, rid))
        _write("trends.json", golf_data.compute_trends(conn))
    finally:
        conn.close()

    print(f"Exported {len(rounds)} round(s) + trends to {DATA_DIR}")
    # an index of ids is handy for the static-export build (generateStaticParams)
    ids = [r["scorecard_id"] for r in rounds]
    _write("round-ids.json", ids)
    print(f"  round ids: {ids}")


if __name__ == "__main__":
    main()

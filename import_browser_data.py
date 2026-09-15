"""Import golf data exported by browser_fetch.js into the pipeline.

The browser export (garmin-golf-export.json) contains the SAME JSON shapes the
Garmin API returns, so we just split it into garmin_out/ files that parse.py
already consumes, then rebuild the DB and the static data.

Usage:
    python import_browser_data.py garmin-golf-export.json
    python import_browser_data.py                # defaults to that filename
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "garmin_out")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "garmin-golf-export.json"
    if not os.path.exists(src):
        sys.exit(f"File not found: {src}\nDownload it first with browser_fetch.js.")

    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    scorecards = data.get("scorecards") or {}
    shots = data.get("shots") or {}
    if not scorecards:
        sys.exit("No 'scorecards' in the export — the browser fetch didn't return "
                 "data. Re-run browser_fetch.js and check the console for errors.")

    os.makedirs(OUT, exist_ok=True)

    def dump(name, obj):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, default=str)

    if data.get("summary") is not None:
        dump("golf_summary.json", data["summary"])
    for sid, detail in scorecards.items():
        dump(f"scorecard_{sid}.json", detail)
    for sid, shot in shots.items():
        dump(f"shots_{sid}.json", shot)

    print(f"Imported {len(scorecards)} round(s) into garmin_out/.")

    # Rebuild the DB and the static site data.
    print("Running parse.py ...")
    subprocess.run([sys.executable, "parse.py"], check=True, cwd=HERE)
    print("Running export_static.py ...")
    subprocess.run([sys.executable, "export_static.py"], check=True, cwd=HERE)

    print("\nDone. Now publish:")
    print('  git add -A && git commit -m "Update golf data" && git push')


if __name__ == "__main__":
    main()

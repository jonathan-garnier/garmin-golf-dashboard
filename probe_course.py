"""READ-ONLY probe: discover a Garmin course-map endpoint that returns the
*current* course definition (par + green/hole coordinates) for a courseGlobalId.

Nothing is modified on Garmin's side — these are all GET requests. Uses the
cached token from fetch_golf.py (no re-login / no 429 if a token exists).

Run:
    python probe_course.py                 # defaults to Cammeray (gid 19704)
    python probe_course.py 19704 211822    # gid, snapshotId

Any successful response is saved to garmin_out/course_probe__<label>.json for
Claude to inspect. A summary table of status per endpoint is printed.
"""
import json
import os
import sys

from fetch_golf import make_client, OUT, save  # reuse token-cached client


def main():
    gid = sys.argv[1] if len(sys.argv) > 1 else "19704"
    snap = sys.argv[2] if len(sys.argv) > 2 else "211822"
    G = "/gcs-golfcommunity/api/v2"

    # (label, path, params) — ordered by likelihood. All GET, all read-only.
    candidates = [
        ("course_gid",            f"{G}/course/{gid}", None),
        ("course_gid_cmap",       f"{G}/course/{gid}/cmap", None),
        ("course_gid_holes",      f"{G}/course/{gid}/hole", None),
        ("coursemap_gid",         f"{G}/coursemap/{gid}", None),
        ("course_detail_q",       f"{G}/course/detail", {"course-id": gid}),
        ("course_snapshot",       f"{G}/course/snapshot/{snap}", None),
        ("coursesnapshot_id",     f"{G}/coursesnapshot/{snap}", None),
        ("course_gid_snapshot",   f"{G}/course/{gid}/snapshot", None),
        ("course_search",         f"{G}/course/search", {"search-terms": "Cammeray"}),
        ("course_info",           f"{G}/course-info/{gid}", None),
        ("greenview_gid",         f"{G}/course/{gid}/green", None),
    ]

    client = make_client()
    print(f"\nProbing course endpoints for gid={gid}, snapshot={snap}\n" + "-" * 60)
    results = []
    for label, path, params in candidates:
        try:
            res = client.connectapi(path, params=params)
            ok = isinstance(res, (dict, list))
            n = len(res) if hasattr(res, "__len__") else "?"
            print(f"  [200] {label:22} {path}  (keys/len={n})")
            save(f"course_probe__{label}.json", res)
            results.append((label, "200", path))
        except Exception as e:
            msg = str(e)
            # surface the HTTP code if present
            code = "ERR"
            for c in ("400", "401", "403", "404", "500"):
                if c in msg:
                    code = c
                    break
            print(f"  [{code}] {label:22} {path}")
            results.append((label, code, path))

    print("-" * 60)
    hits = [r for r in results if r[1] == "200"]
    if hits:
        print(f"{len(hits)} endpoint(s) returned data — saved to garmin_out/. "
              "Tell Claude to inspect course_probe__*.json")
    else:
        print("No course endpoint responded. We'll fall back to a local "
              "par override (and manual green positions if needed).")


if __name__ == "__main__":
    main()

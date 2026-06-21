"""Dump full contents of specific (unknown) message types from a FIT file,
decoding any semicircle lat/long fields to degrees.

Usage: python dump_unknown.py <file.fit> 325 326 327 104 288 22 140 141 79
"""
import sys
import fitdecode

path = sys.argv[1]
targets = set(f"unknown_{n}" for n in sys.argv[2:]) or {
    "unknown_325", "unknown_326", "unknown_327",
    "unknown_104", "unknown_288", "unknown_22", "unknown_140", "unknown_141", "unknown_79",
}

def deg(v):
    return round(v * (180.0 / 2**31), 6) if isinstance(v, int) else v

shown = {t: 0 for t in targets}
CAP = 20

with fitdecode.FitReader(path) as fit:
    for frame in fit:
        if not isinstance(frame, fitdecode.FitDataMessage):
            continue
        if frame.name not in targets:
            continue
        if shown[frame.name] >= CAP:
            continue
        shown[frame.name] += 1
        row = {}
        for fld in frame.fields:
            v = fld.value
            if isinstance(v, int) and ("lat" in fld.name or "long" in fld.name or abs(v) > 1.5e9):
                row[f"{fld.name}"] = f"{v} ({deg(v)})"
            else:
                row[fld.name] = v
        print(f"[{frame.name} #{shown[frame.name]}] {row}")

print("\nshown:", shown)

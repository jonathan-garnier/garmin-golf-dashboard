"""
FIT file inspector — dumps every message type and field found in a Garmin
golf .FIT file so we can see exactly what the Fenix 6 records.

Usage:
    python inspect_fit.py <path-to-file.fit>
    python inspect_fit.py            # auto-picks the first *.fit in this folder

Output:
    - A summary: count of each message type ("frame name")
    - For each message type, the set of field names seen and one sample value
    - Golf-relevant messages (records w/ GPS, hole/lap, anything with "shot")
      printed in full so we can map the schema.
"""
import sys
import glob
import os
from collections import defaultdict, OrderedDict

import fitdecode


def semicircles_to_deg(v):
    """FIT stores lat/long as 'semicircles' int32. Convert to degrees."""
    if v is None:
        return None
    return v * (180.0 / 2**31)


def find_fit():
    if len(sys.argv) > 1:
        return sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    hits = sorted(glob.glob(os.path.join(here, "*.fit")) +
                  glob.glob(os.path.join(here, "*.FIT")))
    if not hits:
        sys.exit("No .fit file given and none found in this folder.\n"
                 "Copy a round from the watch (GARMIN\\Activity\\*.fit) here, "
                 "or pass a path: python inspect_fit.py <file>")
    return hits[0]


def main():
    path = find_fit()
    print(f"Inspecting: {path}\n" + "=" * 70)

    msg_counts = defaultdict(int)
    fields_by_msg = defaultdict(OrderedDict)   # msg -> {field: sample_value}
    interesting = defaultdict(list)            # msg -> list of full dicts

    INTEREST = ("record", "lap", "session", "hole", "shot", "length", "split")

    with fitdecode.FitReader(path) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            name = frame.name
            msg_counts[name] += 1
            row = {}
            for fld in frame.fields:
                row[fld.name] = fld.value
                if fld.name not in fields_by_msg[name]:
                    fields_by_msg[name][fld.name] = fld.value
            # capture full rows for golf-relevant messages (cap to keep output sane)
            if any(k in name for k in INTEREST) and len(interesting[name]) < 8:
                interesting[name].append(row)

    print("\nMESSAGE TYPE COUNTS")
    print("-" * 70)
    for name, n in sorted(msg_counts.items(), key=lambda x: -x[1]):
        print(f"  {name:<28} {n:>6}")

    print("\nFIELDS PER MESSAGE TYPE (field = sample value)")
    print("-" * 70)
    for name in sorted(fields_by_msg):
        print(f"\n[{name}]  (x{msg_counts[name]})")
        for fld, val in fields_by_msg[name].items():
            sval = repr(val)
            if len(sval) > 60:
                sval = sval[:57] + "..."
            print(f"    {fld:<28} = {sval}")

    print("\n\nGOLF-RELEVANT MESSAGE SAMPLES (full rows)")
    print("=" * 70)
    for name in sorted(interesting):
        print(f"\n### {name} (showing up to 8 of {msg_counts[name]}) ###")
        for row in interesting[name]:
            # decode any lat/long on the fly for readability
            for k in list(row):
                if "position_lat" in k and isinstance(row[k], int):
                    row[k + "_deg"] = round(semicircles_to_deg(row[k]), 6)
                if "position_long" in k and isinstance(row[k], int):
                    row[k + "_deg"] = round(semicircles_to_deg(row[k]), 6)
            print("  " + str(row))


if __name__ == "__main__":
    main()

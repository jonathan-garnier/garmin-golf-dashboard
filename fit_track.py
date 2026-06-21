"""Parse a Garmin .fit golf activity into a GPS track, and match a FIT file
to a scorecard by device serial + start time.

A golf FIT does NOT contain the scorecard/shots (those come from Connect); we
use it only for the continuous walk path + heart rate overlay.
"""
import glob
import os

import fitdecode

from util import semi_to_deg, parse_iso

HERE = os.path.dirname(os.path.abspath(__file__))


def read_fit(path):
    """Return {'serial', 'start_time' (datetime), 'track': [points]}.

    Each point: {t (iso str), lat, lon, altitude, heart_rate}.
    """
    serial = None
    start_time = None
    track = []
    with fitdecode.FitReader(path) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            if frame.name == "file_id":
                if frame.has_field("serial_number"):
                    serial = frame.get_value("serial_number")
                if frame.has_field("time_created"):
                    start_time = frame.get_value("time_created")
            elif frame.name == "session" and frame.has_field("start_time"):
                start_time = frame.get_value("start_time") or start_time
            elif frame.name == "record":
                def gv(name):
                    return frame.get_value(name) if frame.has_field(name) else None
                lat, lon = gv("position_lat"), gv("position_long")
                if lat is None or lon is None:
                    continue  # indoor/no-fix points: skip
                t = gv("timestamp")
                track.append({
                    "t": t.isoformat() if t else None,
                    "lat": semi_to_deg(lat),
                    "lon": semi_to_deg(lon),
                    "altitude": gv("enhanced_altitude") or gv("altitude"),
                    "heart_rate": gv("heart_rate"),
                })
    return {"serial": serial, "start_time": start_time, "track": track}


def match_fit_to_round(fit_dir, serial, start_time_iso, max_seconds=900):
    """Find the .fit in fit_dir matching a scorecard.

    Match on device serial (== scorecard unitId) and start time within
    max_seconds. Returns the file path, or None.
    """
    target = parse_iso(start_time_iso)
    serial = str(serial) if serial is not None else None
    best, best_dt = None, None
    for path in glob.glob(os.path.join(fit_dir, "*.fit")) + \
            glob.glob(os.path.join(fit_dir, "*.FIT")):
        try:
            meta = read_fit_meta(path)
        except Exception:
            continue
        if serial and meta["serial"] is not None and str(meta["serial"]) != serial:
            continue
        if target and meta["start_time"]:
            dt = abs((meta["start_time"] - target).total_seconds())
            if dt <= max_seconds and (best_dt is None or dt < best_dt):
                best, best_dt = path, dt
        elif best is None:
            best = path  # serial matched, no time info — accept tentatively
    return best


def read_fit_meta(path):
    """Cheap header read: just serial + start_time, without the full track."""
    serial = None
    start_time = None
    with fitdecode.FitReader(path) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            if frame.name == "file_id":
                if frame.has_field("serial_number"):
                    serial = frame.get_value("serial_number")
                if frame.has_field("time_created"):
                    start_time = frame.get_value("time_created")
            elif frame.name == "session" and frame.has_field("start_time"):
                start_time = frame.get_value("start_time") or start_time
                break  # session is near the end; we have what we need
    return {"serial": serial, "start_time": start_time}


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else \
        (glob.glob(os.path.join(HERE, "*.fit")) or [None])[0]
    if not p:
        sys.exit("No .fit file found.")
    data = read_fit(p)
    print(f"file={p}\nserial={data['serial']} start={data['start_time']} "
          f"points={len(data['track'])}")
    if data["track"]:
        print("first:", data["track"][0])
        print("last :", data["track"][-1])

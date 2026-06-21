"""Shared helpers: coordinate + time conversions.

Two coordinate encodings appear in Garmin golf data:
  - semicircles  (scorecard/shot lat-lon, FIT positions):  deg = v * 180 / 2**31
  - microdegrees (course-snapshot lat/lon):                deg = v / 1e6
"""
from datetime import datetime, timezone

_SEMI = 180.0 / 2**31


def semi_to_deg(v):
    """Semicircles -> decimal degrees."""
    if v is None:
        return None
    return v * _SEMI


def microdeg_to_deg(v):
    """Microdegrees -> decimal degrees."""
    if v is None:
        return None
    return v / 1e6


def epoch_ms_to_iso(ms):
    """Garmin shotTime is epoch milliseconds (UTC)."""
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()


def parse_iso(s):
    """Parse an ISO-8601 string (handles trailing 'Z') to aware datetime."""
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def hole_pars(holepars_str):
    """'443443443' -> {1:4, 2:4, 3:3, ...}. Returns {} if unusable."""
    if not holepars_str or not holepars_str.isdigit():
        return {}
    return {i + 1: int(ch) for i, ch in enumerate(holepars_str)}

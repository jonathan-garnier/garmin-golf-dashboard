"""SQLite layer for the golf dashboard: schema + load/query helpers.

All coordinates are stored as DECIMAL DEGREES (conversions done in parse.py).
"""
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "golf.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
    scorecard_id     INTEGER PRIMARY KEY,
    start_time       TEXT,
    course_name      TEXT,
    course_global_id INTEGER,
    tee_box          TEXT,
    player_handicap  INTEGER,
    holes_completed  INTEGER,
    round_par        INTEGER,
    strokes          INTEGER,
    distance_walked  INTEGER,
    course_lat       REAL,
    course_lon       REAL,
    fit_file         TEXT
);

CREATE TABLE IF NOT EXISTS holes (
    scorecard_id   INTEGER,
    hole_number    INTEGER,
    par            INTEGER,
    strokes        INTEGER,
    handicap_score INTEGER,
    fairway_outcome TEXT,
    pin_lat        REAL,
    pin_lon        REAL,
    PRIMARY KEY (scorecard_id, hole_number)
);

CREATE TABLE IF NOT EXISTS shots (
    shot_id            INTEGER PRIMARY KEY,
    scorecard_id       INTEGER,
    hole_number        INTEGER,
    shot_order         INTEGER,
    shot_time          TEXT,
    shot_type          TEXT,
    club_id            INTEGER,
    meters             REAL,
    start_lat          REAL,
    start_lon          REAL,
    start_lie          TEXT,
    end_lat            REAL,
    end_lon            REAL,
    end_lie            TEXT,
    auto_shot_type     TEXT,
    exclude_from_stats INTEGER
);

CREATE TABLE IF NOT EXISTS track_points (
    scorecard_id INTEGER,
    t            TEXT,
    lat          REAL,
    lon          REAL,
    altitude     REAL,
    heart_rate   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_holes_round ON holes(scorecard_id);
CREATE INDEX IF NOT EXISTS idx_shots_round ON shots(scorecard_id, hole_number);
CREATE INDEX IF NOT EXISTS idx_track_round ON track_points(scorecard_id);
"""


def connect(path=DB_PATH, check_same_thread=True):
    # Streamlit reruns may execute on a different thread than the one that
    # opened the (cached) connection; the app is read-only, so allow it.
    conn = sqlite3.connect(path, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def clear_round(conn, scorecard_id):
    """Remove a round and its children so a re-load is idempotent."""
    for tbl in ("rounds", "holes", "shots", "track_points"):
        conn.execute(f"DELETE FROM {tbl} WHERE scorecard_id = ?", (scorecard_id,))


def upsert_round(conn, r):
    cols = ", ".join(r.keys())
    qs = ", ".join("?" for _ in r)
    conn.execute(f"INSERT OR REPLACE INTO rounds ({cols}) VALUES ({qs})",
                 list(r.values()))


def insert_rows(conn, table, rows):
    if not rows:
        return
    cols = list(rows[0].keys())
    collist = ", ".join(cols)
    qs = ", ".join("?" for _ in cols)
    conn.executemany(
        f"INSERT OR REPLACE INTO {table} ({collist}) VALUES ({qs})",
        [[row[c] for c in cols] for row in rows],
    )


# ---- query helpers used by the app (return plain dict rows) ----

def list_rounds(conn):
    cur = conn.execute(
        "SELECT * FROM rounds ORDER BY start_time DESC")
    return [dict(r) for r in cur.fetchall()]


def get_round(conn, scorecard_id):
    cur = conn.execute("SELECT * FROM rounds WHERE scorecard_id = ?",
                       (scorecard_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def get_holes(conn, scorecard_id):
    cur = conn.execute(
        "SELECT * FROM holes WHERE scorecard_id = ? ORDER BY hole_number",
        (scorecard_id,))
    return [dict(r) for r in cur.fetchall()]


def get_shots(conn, scorecard_id, hole_number=None):
    if hole_number is None:
        cur = conn.execute(
            "SELECT * FROM shots WHERE scorecard_id = ? "
            "ORDER BY hole_number, shot_order", (scorecard_id,))
    else:
        cur = conn.execute(
            "SELECT * FROM shots WHERE scorecard_id = ? AND hole_number = ? "
            "ORDER BY shot_order", (scorecard_id, hole_number))
    return [dict(r) for r in cur.fetchall()]


def get_track(conn, scorecard_id):
    cur = conn.execute(
        "SELECT * FROM track_points WHERE scorecard_id = ? ORDER BY t",
        (scorecard_id,))
    return [dict(r) for r in cur.fetchall()]

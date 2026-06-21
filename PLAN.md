# Garmin Golf Dashboard — Plan

A personal dashboard for golf rounds played with a **Garmin Fenix 6**. It shows,
for each round, where every (detected) shot was hit on a map, lets you drill into
individual rounds, and tracks trends over time.

- **Stack:** FastAPI (JSON API) + Next.js/React/Tailwind frontend (`web/`).
  *(Originally Streamlit; migrated to React/Next.js for a more modern UI. The
  Streamlit prototype `app.py`/`golf_map.py` is kept but superseded.)*
- **Ingestion:** Garmin Connect scrape (`garminconnect` library) + local `.fit` files
- **Storage:** SQLite (`golf.db`)
- **Auth:** password is **never stored**; first run prompts (email/password/MFA),
  then only an expiring OAuth session token is cached in `./.garmin_tokens/`

---

## 1. Why two data sources

We verified against real rounds that the **FIT activity file does NOT contain a
scorecard or labeled shots** — only the GPS walk-path and sensor data. The
scorecard and AutoShot data live in **Garmin Connect**. So each round is assembled
from two sources, joined on scorecard ID / device unit ID / start time:

| Need | Source |
|------|--------|
| Hole scores, par, pins, fairway outcome, **shot start/end coordinates** | Garmin Connect golf API |
| Continuous GPS walk path, heart rate, timing | FIT file (`*.fit`) |

---

## 2. Confirmed data schema

### 2.1 Garmin Connect golf endpoints (`gcs-golfcommunity/api/v2`)

- `get_golf_summary()` → list of scorecards: `id`, `startTime`, `courseName`, etc.
- `get_golf_scorecard(id)` → detail:
  - `scorecardDetails[0].scorecard`: `strokes`, `playerHandicap`, `teeBox`,
    `distanceWalked`, `holesCompleted`, `holes[]`
    - per hole: `number`, `strokes`, `handicapScore`, `fairwayShotOutcome`
      (LEFT/RIGHT/HIT), `pinPositionLat/Lon` — **par is null here**
  - `scorecardDetails[0].shotCounts`: list aligned to holes, e.g. `[2,11,0,...]`
  - `courseSnapshots[0]`: `holePars` (e.g. `'443443443'`), `roundPar`,
    `name`, address, `lat`/`lon`, `tees[]`
- `get_golf_shot_data(id, hole_numbers="N")` → **one hole per call** (lists 400!):
  - `holeShots[].pinPosition` `{lat,lon}`
  - `holeShots[].shots[]`: `shotOrder`, `shotTime`, `clubId`, `autoShotType`,
    `shotType` (APPROACH/CHIP/...), `meters`, `excludeFromStats`,
    `startLoc {lat,lon,lie,lieSource}`, `endLoc {lat,lon,lie,lieSource}`
    - `lie` ∈ TeeBox / Fairway / Rough / Green / ...

### 2.2 FIT file (`fitdecode`)

- `record` messages: `position_lat/long`, `enhanced_altitude`, `heart_rate`,
  `enhanced_speed`, `timestamp` (the walk path)
- `session`: `start_time`, `total_distance`, `nec_lat/long` + `swc_lat/long`
  (course bounding box), `unitId`/serial — used to match FIT ↔ scorecard

### 2.3 Coordinate encodings (IMPORTANT — two different ones)

- Scorecard & shot lat/lon, and FIT positions = **semicircles**: `deg = v * 180 / 2³¹`
- Course-snapshot `lat`/`lon` = **microdegrees**: `deg = v / 1e6`

---

## 3. Known limitations (design around these)

- **AutoShot is sparse:** many holes record zero shots (Cammeray round logged
  shots on only 2 of 9 holes). The map must work with partial/zero shots.
- **AutoShot is noisy:** hole 2 logged 11 shots against a score of 5 — practice
  swings / walking get mis-detected. Filter with `excludeFromStats`, `shotOrder`,
  and a sanity cap (shots shouldn't exceed strokes by much).
- **No club data** unless CT10 sensors are used (`clubId` is 0 here).
- **No putt detection** (Fenix limitation) — putts are scored but not mapped.
- **Garmin rate-limits logins** (429) → token caching is required, not optional.
- **9-hole courses** exist (Cammeray) — never assume 18; derive hole count.

---

## 4. Architecture

```
garmin_golf/
  fetch_golf.py     [done]  Connect sync: login (token cache) → summary →
                            per-round detail → per-hole shots → garmin_out/*.json
  fit_track.py      [todo]  Parse a .fit → GPS path (lat/lon/alt/hr/time);
                            match a FIT file to a scorecard by unitId + start time
  parse.py          [todo]  Normalize garmin_out/*.json (+ FIT tracks) into SQLite,
                            applying the two coordinate conversions and joining par
  db.py             [todo]  SQLite schema + load/query helpers
  app.py            [todo]  Streamlit UI (3 views below)
  golf.db           [gen]   Local store, grows as rounds are synced
  garmin_out/       [gen]   Raw JSON cache (gitignored)
  .garmin_tokens/   [gen]   OAuth token cache (gitignored)
```

Data flow: `fetch_golf.py` (+ FIT files) → `parse.py` → `golf.db` → `app.py`.

### 4.1 SQLite schema (draft)

```sql
rounds(
  scorecard_id PK, start_time, course_name, course_global_id,
  tee_box, player_handicap, holes_completed, round_par,
  strokes, distance_walked, fit_file, course_lat, course_lon
)
holes(
  scorecard_id FK, hole_number, par, strokes, handicap_score,
  fairway_outcome, pin_lat, pin_lon,
  PRIMARY KEY (scorecard_id, hole_number)
)
shots(
  shot_id PK, scorecard_id FK, hole_number, shot_order,
  shot_time, shot_type, club_id, meters,
  start_lat, start_lon, start_lie,
  end_lat, end_lon, end_lie,
  auto_shot_type, exclude_from_stats
)
track_points(
  scorecard_id FK, t, lat, lon, altitude, heart_rate
)
```

All coords stored as **decimal degrees** (conversions done in `parse.py`).

---

## 5. Streamlit views

### View 1 — Rounds list (landing)
- Table/cards of every round: date, course, score vs par (e.g. `41 (+8)`),
  holes played, # shots mapped.
- Sort/filter by course or date. Click a row → Round detail.

### View 2 — Round detail (the centerpiece)
- **Map** (folium + **Esri World Imagery** satellite tiles — free, no token):
  - thin line = FIT walk path
  - **shot vectors** start→end, arrowed, colored by lie or shot type,
    tooltip = distance + club + type
  - pin markers per hole
  - hole selector to zoom to one hole; "noise filter" toggle (hide
    `excludeFromStats` / over-count shots)
- **Hole table:** par, strokes, +/-, fairway outcome, shots detected.
- Round summary header: score vs par, fairways hit, distance walked, total time.

### View 3 — Trends (improves as more rounds sync)
- Score vs par over time (line).
- Per-hole scoring average for a given course (which holes cost you strokes).
- Shot-distance distribution by shot type (box/violin).
- Fairway accuracy % over time (from `fairwayShotOutcome`).
- Round count, best/worst, scoring average — KPI tiles.

---

## 6. Build phases

1. **Data foundation** — `db.py`, `parse.py`, `fit_track.py`; load the Cammeray
   round end-to-end into `golf.db`. Verify counts and coordinate conversions.
2. **Shot map** — `app.py` Round-detail view with the folium satellite map,
   walk path, shot vectors, pins, hole selector + noise filter.
3. **Rounds list + navigation** — landing view, click-through to detail.
4. **Trends** — View 3 charts over all synced rounds.
5. **Sync UX** — a "Sync from Garmin" action / instructions; backfill all 5
   existing rounds; document the FIT-import step.
6. **Polish** — noise-filter tuning, caching, empty-state handling for
   shotless holes, styling.

---

## 7. Open questions / risks

- **FIT ↔ scorecard matching:** match on `unitId` + nearest `start_time`. Need to
  confirm FIT filenames/timestamps line up for all rounds (only have 1 FIT now).
- **Bulk FIT retrieval:** Connect can also serve activity FITs; decide whether to
  download FITs via the API or keep manual USB copy. (Walk path is a nice-to-have;
  shot map works without it.)
- **Noise filtering heuristic:** needs tuning against a few real rounds.
- **Rate limiting:** keep sync infrequent; rely on token cache; sync only new
  scorecard IDs not already in `golf.db`.
- **Course par for 18-hole courses:** confirm `holePars` length matches holes.

---

## 8. Status

- [x] Confirmed FIT contents and limitations (`inspect_fit.py`, `dump_unknown.py`)
- [x] Confirmed Connect golf endpoints return shots with start/end coords + lie
- [x] `fetch_golf.py` — token-cached sync, **backfills all rounds**, per-hole shots
- [x] `util.py`, `db.py`, `fit_track.py`, `parse.py` — data foundation (Phase 1),
      verified end-to-end against a real round (par join, coord conversions, FIT match)
- [x] Streamlit prototype (`app.py`, `golf_map.py`) — superseded, kept for reference
- [x] **All 5 rounds backfilled** and loaded into `golf.db` (incl. Moore Park 360966133)
- [x] **Migrated to React/Next.js + FastAPI** — `api.py` (JSON API) + `web/`
      (Next 16, Tailwind v4, react-leaflet satellite map, Recharts). All 3 views
      verified in-browser: Rounds list, Round detail (Moore Park 18-hole shot map
      renders on satellite imagery), Trends (score-vs-par area + scoring + shot
      distance charts). Production build passes.
- [ ] Tune the noise filter against real rounds (hole-2 false-shot type cases)
- [ ] Decide FIT retrieval (USB vs API) for walk-path on older rounds
- [ ] Optional: auth on the API if ever exposed beyond localhost

### How to run
```
python fetch_golf.py                 # backfill rounds -> garmin_out/ (token cached)
python parse.py                      # build golf.db
python -m uvicorn api:app --port 8000 # terminal 1: API
cd web && npm run dev                 # terminal 2: frontend -> http://localhost:3000
```
See README.md for setup details.
```

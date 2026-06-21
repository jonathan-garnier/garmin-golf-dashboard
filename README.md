# Garmin Golf Dashboard

Personal dashboard for golf rounds played with a **Garmin Fenix 6** — a shot-by-shot
map of every round, drill-down per round, and trends over time.

## Architecture

```
Garmin Connect  ─┐
                 ├─► fetch_golf.py ─► garmin_out/*.json ─┐
watch .fit files ┘                                       ├─► parse.py ─► golf.db ─► api.py (FastAPI) ─► web/ (Next.js)
                  fit_track.py ─────────────────────────┘
```

- **Data pipeline (Python):** `fetch_golf.py` (Garmin Connect sync, token-cached),
  `fit_track.py` (FIT walk-path), `parse.py` → SQLite `golf.db`.
- **API (Python/FastAPI):** `api.py` serves JSON from `golf.db` on `:8000`.
- **Frontend (Next.js + Tailwind):** `web/` — React app on `:3000` with a Leaflet
  satellite shot map (free Esri tiles) and Recharts trends.

See `PLAN.md` for the full design and the confirmed data schema.

## Setup (once)

```powershell
# Python backend
python -m pip install -r requirements.txt

# Frontend
cd web; npm install; cd ..
```

## Refresh data

```powershell
python fetch_golf.py     # pull rounds from Garmin Connect (prompts login once; token cached)
python parse.py          # (re)build golf.db from cached JSON + matched FIT files
```

## Run the dashboard (two terminals)

```powershell
# Terminal 1 — API
python -m uvicorn api:app --port 8000

# Terminal 2 — web
cd web; npm run dev
```

Then open **http://localhost:3000**.

- The frontend expects the API at `http://localhost:8000`. To change it, set
  `NEXT_PUBLIC_API_BASE` (e.g. in `web/.env.local`). The API's CORS currently
  allows `localhost:3000` — update `api.py` if you change the frontend port.

## Notes / known limitations

- **AutoShot is sparse & noisy.** Some holes record no shots; some log false
  swings. Use the "Hide noisy shots" toggle (filters `excludeFromStats`).
- **Walk path needs the FIT file.** Only rounds whose `.fit` is present locally
  show the GPS path; shots + pins come from Connect and always render.
- **Manually-entered scorecards** (e.g. the Cammeray test round) have unreliable
  shot/course mapping — Moore Park (played live) is the good reference round.
- The original Streamlit prototype (`app.py`, `golf_map.py`) is kept but
  superseded by `web/`.

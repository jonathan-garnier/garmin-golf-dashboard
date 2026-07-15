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
python export_static.py  # export golf.db -> web/public/data/*.json (for the hosted build)
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

## Hosting (GitHub Pages)

The dashboard is read-only, so it's deployed as a **static site** — no server.
`export_static.py` writes the data to `web/public/data/*.json`, the Next.js app
builds with `output: export`, and `.github/workflows/deploy.yml` publishes it to
GitHub Pages on every push to `main`.

Live URL: **https://jonathan-garnier.github.io/garmin-golf-dashboard/**

**One-time setup:** in the repo on GitHub → **Settings → Pages → Build and
deployment → Source: GitHub Actions**.

**To publish new rounds:**
```powershell
python fetch_golf.py
python parse.py
python export_static.py        # refresh the bundled JSON
git add -A; git commit -m "Update golf data"; git push
```
The push triggers the Actions workflow, which rebuilds and redeploys (~1–2 min).

Two data modes share one frontend: local `npm run dev` reads the live FastAPI
backend; the hosted build (`NEXT_PUBLIC_STATIC=1`, set by the workflow) reads the
bundled JSON. `NEXT_PUBLIC_BASE_PATH` in the workflow must match the repo name.

### Update from your phone

The **Update golf data** workflow (`.github/workflows/update-data.yml`) pulls
your latest rounds from Garmin Connect and redeploys — no computer needed.
Trigger it from the GitHub mobile app or website: **repo → Actions → "Update
golf data" → Run workflow**.

**One-time setup — store your Garmin session token as a secret:**

1. Log in once locally so the token exists (`python fetch_golf.py`).
2. Print the token as base64 (run locally; do not share the output):
   ```powershell
   python -c "import base64;print(base64.b64encode(open('.garmin_tokens/garmin_tokens.json','rb').read()).decode())"
   ```
3. In the repo → **Settings → Secrets and variables → Actions → New repository
   secret** → name **`GARMIN_TOKEN_B64`**, value = the string from step 2.

**Notes:**
- The token grants read access to your Garmin account. It's an encrypted GitHub
  secret and masked in logs, but it lives in a public repo's settings — revoke by
  changing your Garmin password. It lasts months; when it expires the workflow
  fails with a clear message — just redo steps 1–3.
- Phone refreshes include scores + shots (from Garmin Connect) but **not FIT walk
  paths** (those need the watch plugged into your PC — refresh locally for those).

## Notes / known limitations

- **AutoShot is sparse & noisy.** Some holes record no shots; some log false
  swings. Use the "Hide noisy shots" toggle (filters `excludeFromStats`).
- **Walk path needs the FIT file.** Only rounds whose `.fit` is present locally
  show the GPS path; shots + pins come from Connect and always render.
- **Manually-entered scorecards** (e.g. the Cammeray test round) have unreliable
  shot/course mapping — Moore Park (played live) is the good reference round.
- The original Streamlit prototype (`app.py`, `golf_map.py`) is kept but
  superseded by `web/`.

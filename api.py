"""FastAPI JSON backend for the golf dashboard (local development).

Thin layer over golf_data.py — the Next.js frontend consumes these endpoints
during local dev. For hosting, the same data is exported to static JSON by
export_static.py and served by GitHub Pages (no server needed).

Run:  python -m uvicorn api:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import db
import golf_data

app = FastAPI(title="Garmin Golf API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _conn():
    return db.connect(check_same_thread=False)


@app.get("/api/rounds")
def list_rounds():
    conn = _conn()
    try:
        return golf_data.compute_rounds(conn)
    finally:
        conn.close()


@app.get("/api/rounds/{rid}")
def round_detail(rid: int):
    conn = _conn()
    try:
        detail = golf_data.compute_round_detail(conn, rid)
    finally:
        conn.close()
    if detail is None:
        raise HTTPException(404, "round not found")
    return detail


@app.get("/api/trends")
def trends():
    conn = _conn()
    try:
        return golf_data.compute_trends(conn)
    finally:
        conn.close()


@app.get("/api/health")
def health():
    return {"ok": True}

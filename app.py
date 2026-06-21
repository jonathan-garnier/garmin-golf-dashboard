"""Garmin Golf dashboard (Streamlit).

Views:
  - Rounds      : list of all rounds; click to open a round
  - Round detail: satellite shot map + hole-by-hole table
  - Trends      : scoring and shot trends across all rounds

Run:  streamlit run app.py     (after: python parse.py to build golf.db)
"""
import os

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import db
from golf_map import build_round_map, LIE_COLORS

st.set_page_config(page_title="Golf Dashboard", page_icon="⛳", layout="wide")


@st.cache_resource
def _conn():
    return db.connect(check_same_thread=False)


def fmt_vs_par(strokes, par):
    if strokes is None or par is None:
        return "—"
    d = strokes - par
    return f"{strokes} ({'+' if d > 0 else ''}{d})" if d else f"{strokes} (E)"


def fmt_date(iso):
    return (iso or "")[:10]


# ----------------------------------------------------------------------------
def _open_round(scorecard_id):
    """on_click callback: runs BEFORE widgets instantiate next run, so it may
    set the `nav` widget-state safely."""
    st.session_state["round_id"] = scorecard_id
    st.session_state["nav"] = "Round detail"


def view_rounds(conn):
    st.header("⛳ Rounds")
    rounds = db.list_rounds(conn)
    if not rounds:
        st.info("No rounds loaded. Run `python fetch_golf.py` then "
                "`python parse.py` to populate golf.db.")
        return
    for r in rounds:
        c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 2])
        c1.write(f"**{fmt_date(r['start_time'])}**")
        c2.write(r["course_name"] or "—")
        c3.write(fmt_vs_par(r["strokes"], r["round_par"]))
        c4.write(f"{r['holes_completed'] or '?'} holes")
        c5.button("Open", key=f"open_{r['scorecard_id']}",
                  on_click=_open_round, args=(r["scorecard_id"],))


# ----------------------------------------------------------------------------
def view_round_detail(conn):
    rid = st.session_state.get("round_id")
    rounds = db.list_rounds(conn)
    if not rounds:
        st.info("No rounds loaded yet.")
        return
    ids = [r["scorecard_id"] for r in rounds]
    labels = {r["scorecard_id"]:
              f"{fmt_date(r['start_time'])} · {r['course_name']}" for r in rounds}
    if rid not in ids:
        rid = ids[0]
    rid = st.selectbox("Round", ids, index=ids.index(rid),
                       format_func=lambda i: labels[i])
    st.session_state["round_id"] = rid

    rnd = db.get_round(conn, rid)
    holes = db.get_holes(conn, rid)
    shots = db.get_shots(conn, rid)
    track = db.get_track(conn, rid)

    # summary header
    fairways = [h for h in holes if h.get("fairway_outcome")]
    hit = sum(1 for h in fairways if h["fairway_outcome"] == "HIT")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Score", fmt_vs_par(rnd["strokes"], rnd["round_par"]))
    k2.metric("Holes", rnd["holes_completed"] or "?")
    k3.metric("Distance walked", f"{(rnd['distance_walked'] or 0)/1000:.2f} km")
    k4.metric("Fairways hit", f"{hit}/{len(fairways)}" if fairways else "—")

    left, right = st.columns([3, 2])
    with left:
        hole_opts = ["All"] + [h["hole_number"] for h in holes]
        sel = st.selectbox("Focus hole", hole_opts)
        cc1, cc2 = st.columns(2)
        show_track = cc1.checkbox("Show walk path", value=bool(track))
        hide_noise = cc2.checkbox("Hide noisy shots (excluded from stats)",
                                  value=True)
        n_shots = sum(1 for s in shots
                      if not (hide_noise and s.get("exclude_from_stats")))
        if not shots:
            st.caption("No AutoShot data for this round — showing pins"
                       + (" and walk path." if track else "."))
        else:
            st.caption(f"{n_shots} shot(s) shown. "
                       "Colour = lie at shot start.")
        m = build_round_map(rnd, holes, shots, track,
                            selected_hole=None if sel == "All" else sel,
                            show_track=show_track, hide_noise=hide_noise)
        st_folium(m, height=560, width=None,
                  returned_objects=[], key=f"map_{rid}_{sel}")
        # lie legend
        legend = "  ".join(
            f"<span style='color:{c}'>■</span> {name}"
            for name, c in LIE_COLORS.items())
        st.markdown(f"<small>{legend}</small>", unsafe_allow_html=True)

    with right:
        st.subheader("Holes")
        df = pd.DataFrame(holes)
        if not df.empty:
            df["+/-"] = df.apply(
                lambda x: (x["strokes"] - x["par"])
                if x["strokes"] is not None and x["par"] is not None else None,
                axis=1)
            show = df[["hole_number", "par", "strokes", "+/-",
                       "fairway_outcome"]].rename(columns={
                "hole_number": "Hole", "par": "Par", "strokes": "Score",
                "fairway_outcome": "Fairway"})
            st.dataframe(show, hide_index=True, width="stretch")


# ----------------------------------------------------------------------------
def view_trends(conn):
    st.header("📈 Trends")
    rounds = db.list_rounds(conn)
    if len(rounds) < 1:
        st.info("Load rounds first.")
        return
    rdf = pd.DataFrame(rounds)
    rdf["date"] = pd.to_datetime(rdf["start_time"]).dt.tz_localize(None)
    rdf["vs_par"] = rdf["strokes"] - rdf["round_par"]
    rdf = rdf.sort_values("date")

    c1, c2, c3 = st.columns(3)
    c1.metric("Rounds", len(rdf))
    c2.metric("Avg score vs par",
              f"{rdf['vs_par'].mean():+.1f}" if rdf["vs_par"].notna().any()
              else "—")
    c3.metric("Best", f"{rdf['vs_par'].min():+.0f}"
              if rdf["vs_par"].notna().any() else "—")

    st.subheader("Score vs par over time")
    st.line_chart(rdf.set_index("date")["vs_par"])

    # all shots across rounds
    shots = []
    for r in rounds:
        shots.extend(db.get_shots(conn, r["scorecard_id"]))
    sdf = pd.DataFrame(shots)
    if not sdf.empty:
        sdf = sdf[sdf["exclude_from_stats"] == 0]
        st.subheader("Shot distance by type")
        valid = sdf.dropna(subset=["meters", "shot_type"])
        if not valid.empty:
            st.bar_chart(valid.groupby("shot_type")["meters"].mean())
    else:
        st.caption("No shot data yet — trends will fill in as AutoShot rounds "
                   "are added.")


# ----------------------------------------------------------------------------
def main():
    conn = _conn()
    if not os.path.exists(db.DB_PATH):
        st.error("golf.db not found. Run `python parse.py` first.")
        return
    st.sidebar.title("⛳ Golf")
    # Keyed radio is the single source of truth; navigation buttons set
    # st.session_state["nav"] via on_click callbacks (allowed pre-instantiation).
    view = st.sidebar.radio("View", ["Rounds", "Round detail", "Trends"],
                            key="nav")
    if view == "Rounds":
        view_rounds(conn)
    elif view == "Round detail":
        view_round_detail(conn)
    else:
        view_trends(conn)


if __name__ == "__main__":
    main()

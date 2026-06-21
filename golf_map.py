"""Folium map for a single round: satellite basemap + walk path + shot vectors
+ pins. Uses free Esri World Imagery tiles (no Mapbox token required).
"""
import folium
from folium.plugins import PolyLineTextPath

# Colour per lie (where the shot started/landed).
LIE_COLORS = {
    "TeeBox": "#ffffff",
    "Fairway": "#34c759",
    "Rough": "#9acd32",
    "Green": "#7cfc00",
    "Bunker": "#e8d18b",
    "Sand": "#e8d18b",
    "Water": "#3aa0ff",
    "Recovery": "#ff9f0a",
    "OutOfBounds": "#ff453a",
}
DEFAULT_LIE = "#dddddd"

ESRI_IMAGERY = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
ESRI_ATTR = "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics"


def _lie_color(lie):
    return LIE_COLORS.get(lie, DEFAULT_LIE)


def _center(round_row, holes, shots, track):
    """Best available center point for the map."""
    if round_row.get("course_lat"):
        return [round_row["course_lat"], round_row["course_lon"]]
    for src in (shots, holes, track):
        for r in src:
            lat = r.get("start_lat") or r.get("pin_lat") or r.get("lat")
            lon = r.get("start_lon") or r.get("pin_lon") or r.get("lon")
            if lat and lon:
                return [lat, lon]
    return [0, 0]


def build_round_map(round_row, holes, shots, track,
                    selected_hole=None, show_track=True, hide_noise=True):
    center = _center(round_row, holes, shots, track)
    m = folium.Map(location=center, zoom_start=16, tiles=None,
                   control_scale=True)
    folium.TileLayer(tiles=ESRI_IMAGERY, attr=ESRI_ATTR,
                     name="Satellite").add_to(m)

    bounds = []

    if selected_hole is not None:
        holes = [h for h in holes if h["hole_number"] == selected_hole]
        shots = [s for s in shots if s["hole_number"] == selected_hole]
        if show_track:
            track = []  # per-hole track segmentation isn't reliable; skip

    # --- walk path ---
    if show_track and track:
        pts = [[p["lat"], p["lon"]] for p in track if p["lat"] and p["lon"]]
        if pts:
            folium.PolyLine(pts, color="#00e5ff", weight=2, opacity=0.45,
                            tooltip="Walk path").add_to(m)
            bounds.extend(pts)

    # --- pins ---
    for h in holes:
        if h.get("pin_lat"):
            folium.Marker(
                [h["pin_lat"], h["pin_lon"]],
                tooltip=f"Hole {h['hole_number']} pin "
                        f"(par {h.get('par')}, scored {h.get('strokes')})",
                icon=folium.Icon(color="red", icon="flag", prefix="fa"),
            ).add_to(m)
            bounds.append([h["pin_lat"], h["pin_lon"]])

    # --- shot vectors ---
    for s in shots:
        if hide_noise and s.get("exclude_from_stats"):
            continue
        if not (s.get("start_lat") and s.get("end_lat")):
            continue
        a = [s["start_lat"], s["start_lon"]]
        b = [s["end_lat"], s["end_lon"]]
        color = _lie_color(s.get("start_lie"))
        popup = folium.Popup(
            f"<b>Hole {s['hole_number']}</b> shot {s.get('shot_order')}<br>"
            f"{s.get('shot_type')} — {s.get('meters', 0):.0f} m<br>"
            f"{s.get('start_lie')} → {s.get('end_lie')}",
            max_width=220)
        line = folium.PolyLine([a, b], color=color, weight=4, opacity=0.9,
                               popup=popup)
        line.add_to(m)
        PolyLineTextPath(line, "  ►  ", repeat=False, center=True,
                         offset=6, attributes={"fill": color,
                                               "font-size": "14"}).add_to(m)
        folium.CircleMarker(a, radius=4, color=color, fill=True,
                            fill_opacity=1).add_to(m)
        bounds.extend([a, b])

    if bounds:
        m.fit_bounds(bounds, padding=(30, 30))
    return m

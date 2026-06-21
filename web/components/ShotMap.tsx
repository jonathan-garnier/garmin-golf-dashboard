"use client";

import { Fragment, useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Marker,
  Popup,
  Tooltip,
  useMap,
} from "react-leaflet";
import L, { LatLngBoundsExpression, LatLngExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { Hole, Shot, TrackPoint, RoundDetail, lieColor } from "@/lib/api";

const ESRI =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
const ESRI_ATTR = "Tiles © Esri — Maxar, Earthstar Geographics";

function pinIcon() {
  return L.divIcon({
    className: "",
    html: `<div class="pin-icon">⛳</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 22],
  });
}

function FitBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 19 });
    }
  }, [bounds, map]);
  return null;
}

export default function ShotMap({
  data,
  selectedHole,
  showTrack,
  hideNoise,
}: {
  data: RoundDetail;
  selectedHole: number | null;
  showTrack: boolean;
  hideNoise: boolean;
}) {
  const { round, holes, shots, track } = data;

  const holesShown: Hole[] = useMemo(
    () => (selectedHole == null ? holes : holes.filter((h) => h.hole_number === selectedHole)),
    [holes, selectedHole]
  );
  const shotsShown: Shot[] = useMemo(
    () =>
      shots.filter(
        (s) =>
          (selectedHole == null || s.hole_number === selectedHole) &&
          !(hideNoise && s.exclude_from_stats) &&
          s.start_lat != null &&
          s.end_lat != null
      ),
    [shots, selectedHole, hideNoise]
  );
  const trackShown: TrackPoint[] = useMemo(
    () => (showTrack && selectedHole == null ? track.filter((p) => p.lat != null) : []),
    [track, showTrack, selectedHole]
  );

  const bounds = useMemo<LatLngBoundsExpression | null>(() => {
    const pts: LatLngExpression[] = [];
    shotsShown.forEach((s) => {
      pts.push([s.start_lat!, s.start_lon!]);
      pts.push([s.end_lat!, s.end_lon!]);
    });
    holesShown.forEach((h) => h.pin_lat != null && pts.push([h.pin_lat, h.pin_lon!]));
    trackShown.forEach((p) => pts.push([p.lat!, p.lon!]));
    return pts.length ? (pts as LatLngBoundsExpression) : null;
  }, [shotsShown, holesShown, trackShown]);

  const center: LatLngExpression =
    round.course_lat != null ? [round.course_lat, round.course_lon!] : [0, 0];

  return (
    <MapContainer
      center={center}
      zoom={16}
      scrollWheelZoom
      className="h-full w-full"
      style={{ minHeight: 520 }}
    >
      <TileLayer url={ESRI} attribution={ESRI_ATTR} maxZoom={20} />
      <FitBounds bounds={bounds} />

      {trackShown.length > 1 && (
        <Polyline
          positions={trackShown.map((p) => [p.lat!, p.lon!]) as LatLngExpression[]}
          pathOptions={{ color: "#22d3ee", weight: 2, opacity: 0.45 }}
        />
      )}

      {shotsShown.map((s) => {
        const color = lieColor(s.start_lie);
        const a: LatLngExpression = [s.start_lat!, s.start_lon!];
        const b: LatLngExpression = [s.end_lat!, s.end_lon!];
        return (
          <Fragment key={s.shot_id}>
            <Polyline
              positions={[a, b]}
              pathOptions={{ color, weight: 4, opacity: 0.9 }}
            >
              <Popup>
                <strong>Hole {s.hole_number}</strong> · shot {s.shot_order}
                <br />
                {s.shot_type} — {Math.round(s.meters ?? 0)} m
                <br />
                {s.start_lie} → {s.end_lie}
              </Popup>
            </Polyline>
            <CircleMarker
              center={a}
              radius={6}
              pathOptions={{ color, fillColor: color, fillOpacity: 1, weight: 2 }}
            >
              <Tooltip>{`#${s.shot_order} · ${Math.round(s.meters ?? 0)} m`}</Tooltip>
            </CircleMarker>
          </Fragment>
        );
      })}

      {holesShown.map((h) =>
        h.pin_lat != null ? (
          <Marker key={h.hole_number} position={[h.pin_lat, h.pin_lon!]} icon={pinIcon()}>
            <Popup>
              <strong>Hole {h.hole_number}</strong>
              <br />
              Par {h.par ?? "—"} · scored {h.strokes ?? "—"}
            </Popup>
          </Marker>
        ) : null
      )}
    </MapContainer>
  );
}

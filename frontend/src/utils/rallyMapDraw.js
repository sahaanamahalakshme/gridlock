const RALLY_PATH_COLOR = "#DC2626";      // Red — the rally route
const BLOCKED_ROAD_COLOR = "#F97316";    // Orange — affected crossing roads
const DIVERSION_COLOR = "#059669";       // Green — diversion lines
const BARRICADE_EMOJI = "🚧";
 
const LAYER_IDS = [
  "rally-path",
  "rally-path-border",
  "rally-path-glow",
];
 
export function clearRallyLayers(map, markersRef) {
  // Remove all rally-related markers
  if (markersRef?.current) {
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
  }
 
  // Remove all dynamic layers/sources
  const allLayerIds = [
    "rally-path", "rally-path-border",
    "rally-path-glow",
    "impact-circle",
    "diversion-arrow",
  ];
 
  // Also remove per-crossing layers (numbered)
  for (let i = 0; i < 10; i++) {
    allLayerIds.push(
      `crossing-road-${i}`,
      `crossing-road-${i}-border`,
      `diversion-${i}`,
      `diversion-${i}-border`,
    );
  }
 
  allLayerIds.forEach((id) => {
    try {
      if (map.getLayer(id)) map.removeLayer(id);
      if (map.getSource(id)) map.removeSource(id);
    } catch (_) {}
  });
}
 
function upsertLine(map, id, coords, color, width, opacity, dasharray) {
  const geojson = {
    type: "Feature",
    geometry: { type: "LineString", coordinates: coords },
  };
 
  try {
    if (map.getSource(id)) {
      map.getSource(id).setData(geojson);
      return;
    }
  } catch (_) {}
 
  map.addSource(id, { type: "geojson", data: geojson });
 
  // White border underneath for visibility
  map.addLayer({
    id: `${id}-border`,
    type: "line",
    source: id,
    paint: {
      "line-color": "#ffffff",
      "line-width": width + 4,
      "line-opacity": opacity * 0.5,
    },
  });
 
  map.addLayer({
    id,
    type: "line",
    source: id,
    paint: {
      "line-color": color,
      "line-width": width,
      "line-opacity": opacity,
      ...(dasharray ? { "line-dasharray": dasharray } : {}),
    },
  });
}
 
function placeLabel(map, markersRef, lat, lng, text, bgColor) {
  const el = document.createElement("div");
  el.style.cssText = `
    background: ${bgColor};
    color: white;
    font-size: 11px;
    font-weight: 700;
    font-family: Inter, sans-serif;
    padding: 3px 8px;
    border-radius: 4px;
    white-space: nowrap;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    pointer-events: none;
    border: 1.5px solid rgba(255,255,255,0.3);
  `;
  el.textContent = text;
 
  const marker = new window.maplibregl.Marker({ element: el, anchor: "left" })
    .setLngLat([lng, lat])
    .addTo(map);
 
  markersRef.current.push(marker);
}
 
function placeBarricade(map, markersRef, lat, lng, roadName) {
  const el = document.createElement("div");
  el.style.cssText = `
    font-size: 22px;
    line-height: 1;
    cursor: default;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
  `;
  el.innerHTML = BARRICADE_EMOJI;
  el.title = `Barricade: ${roadName}`;
 
  const marker = new window.maplibregl.Marker({ element: el, anchor: "bottom" })
    .setLngLat([lng, lat])
    .addTo(map);
 
  markersRef.current.push(marker);
}
 
function placeDiversionPin(map, markersRef, lat, lng, roadName, direction) {
  const el = document.createElement("div");
  el.style.cssText = `
    background: ${DIVERSION_COLOR};
    color: white;
    font-size: 11px;
    font-weight: 700;
    font-family: Inter, sans-serif;
    padding: 4px 10px;
    border-radius: 99px;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(0,0,0,0.35);
    display: flex;
    align-items: center;
    gap: 4px;
    border: 2px solid white;
  `;
  el.innerHTML = `✓ Divert: ${direction}`;
  el.title = `Diversion for ${roadName}`;
 
  const marker = new window.maplibregl.Marker({ element: el, anchor: "top" })
    .setLngLat([lng, lat])
    .addTo(map);
 
  markersRef.current.push(marker);
}
 
/**
 * Main drawing function — call after analyzeRallyRoute() returns
 *
 * @param {object} map - MapLibre GL map instance
 * @param {object} markersRef - React ref holding array of markers
 * @param {object} analysis - Result from analyzeRallyRoute()
 */
export function drawRallyAnalysis(map, markersRef, analysis) {
  const { rallyPath, rallyRoadName, crossingRoads } = analysis;
 
  // 1. Draw the rally path as a red line
  if (rallyPath && rallyPath.length >= 2) {
    // Glow effect: wide transparent red underneath
    try {
      if (!map.getSource("rally-path-glow")) {
        map.addSource("rally-path-glow", {
          type: "geojson",
          data: {
            type: "Feature",
            geometry: { type: "LineString", coordinates: rallyPath },
          },
        });
        map.addLayer({
          id: "rally-path-glow",
          type: "line",
          source: "rally-path-glow",
          paint: {
            "line-color": RALLY_PATH_COLOR,
            "line-width": 18,
            "line-opacity": 0.15,
          },
        });
      }
    } catch (_) {}
 
    upsertLine(map, "rally-path", rallyPath, RALLY_PATH_COLOR, 5, 0.92);
 
    // Label at midpoint of rally path
    const mid = rallyPath[Math.floor(rallyPath.length / 2)];
    if (mid) {
      placeLabel(
        map, markersRef,
        mid[1], mid[0],
        `  🚨 ${rallyRoadName || "Rally Route"} (Blocked)`,
        RALLY_PATH_COLOR
      );
    }
  }
 
  // 2. For each crossing main road — draw it highlighted, add barricade and diversion
  crossingRoads.forEach((road, i) => {
    const { name, crossingPoint, diversionDirection, geometry } = road;
 
    // Draw the crossing road in orange (the affected section)
    if (geometry && geometry.length >= 2) {
      // Convert [lat, lng] to [lng, lat] for MapLibre
      const coords = geometry.map((p) => [p[1], p[0]]);
      upsertLine(
        map,
        `crossing-road-${i}`,
        coords,
        BLOCKED_ROAD_COLOR,
        4,
        0.85,
        [8, 4]  // dashed to show it's blocked
      );
    }
 
    // Barricade at the crossing point
    if (crossingPoint) {
      placeBarricade(map, markersRef, crossingPoint.lat, crossingPoint.lng, name);
 
      // "ROAD NAME (Blocked)" label
      placeLabel(
        map, markersRef,
        crossingPoint.lat,
        crossingPoint.lng + 0.001,
        `${name} (Blocked)`,
        BLOCKED_ROAD_COLOR
      );
 
      // Diversion instruction below the barricade
      placeDiversionPin(
        map, markersRef,
        crossingPoint.lat - 0.0015,
        crossingPoint.lng,
        name,
        diversionDirection
      );
    }
  });
 
  // 3. Fit map to show everything
  if (rallyPath && rallyPath.length >= 2) {
    const lngs = rallyPath.map((c) => c[0]);
    const lats = rallyPath.map((c) => c[1]);
 
    crossingRoads.forEach((r) => {
      if (r.crossingPoint) {
        lats.push(r.crossingPoint.lat);
        lngs.push(r.crossingPoint.lng);
      }
    });
 
    map.fitBounds(
      [
        [Math.min(...lngs) - 0.008, Math.min(...lats) - 0.008],
        [Math.max(...lngs) + 0.008, Math.max(...lats) + 0.008],
      ],
      { padding: 70, duration: 900 }
    );
  }
}
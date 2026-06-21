// rallyRouteAnalysis.js — OFFLINE / CACHE-ONLY
//
// Architecture:
//   click → bangalore_road_cache.json → nearest roads → crossing roads
//          → parallel roads → diversion instructions → drawRallyAnalysis()
//
// ✅ No Overpass   ✅ No OSRM   ✅ No 429   ✅ No 504   ✅ Works offline

// ─────────────────────────────────────────────────────────────────────────
// ROAD CLASSIFICATION
// ─────────────────────────────────────────────────────────────────────────

const MAIN_ROAD_TYPES = new Set([
  "motorway", "motorway_link",
  "trunk", "trunk_link",
  "primary", "primary_link",
  "secondary", "secondary_link",
  "tertiary", "tertiary_link",
]);

const LOCAL_STREET_PATTERNS = [
  /^local street/i,
  /^\d+\.\s/,
  /\bcross road\b/i,
  /\bcross\b/i,
  /^unnamed/i,
  /^#\d+/,
  /^\d+$/,
];

function isMainRoad(name, highway) {
  if (!MAIN_ROAD_TYPES.has(highway)) return false;
  if (!name) return false;
  for (const pattern of LOCAL_STREET_PATTERNS) {
    if (pattern.test(name)) return false;
  }
  return true;
}

// ─────────────────────────────────────────────────────────────────────────
// STEP 2 — ROAD CACHE
// ─────────────────────────────────────────────────────────────────────────

let ROAD_CACHE = null;

async function loadRoadCache() {
  if (ROAD_CACHE) return ROAD_CACHE;

  const res = await fetch("/bangalore_road_cache.json");

  if (!res.ok)
    throw new Error("Could not load bangalore_road_cache.json (status " + res.status + ")");

  ROAD_CACHE = await res.json();

  return ROAD_CACHE;
}

// ─────────────────────────────────────────────────────────────────────────
// STEP 3 — DISTANCE HELPER
// ─────────────────────────────────────────────────────────────────────────

function distanceMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000;

  const dLat = ((lat2 - lat1) * Math.PI) / 180;

  const dLon = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ─────────────────────────────────────────────────────────────────────────
// STEP 4 — CACHED ROADS NEAR A POINT
// ─────────────────────────────────────────────────────────────────────────

function cachedRoadsNear(cache, lat, lng, radius = 250) {
  const roads = cache.roads || [];

  return roads.filter((road) =>
    road.geometry.some(([rLat, rLng]) => {
      return distanceMeters(lat, lng, rLat, rLng) <= radius;
    })
  );
}

// ─────────────────────────────────────────────────────────────────────────
// STEP 5 — CONVERT CACHE ROAD TO OVERPASS SHAPE
// ─────────────────────────────────────────────────────────────────────────

function cachedRoadToOverpassShape(road) {
  return {
    tags: {
      name: road.name,
      highway: road.highway,
    },
    geometry: road.geometry.map(([lat, lng]) => ({
      lat,
      lon: lng,
    })),
  };
}

// ─────────────────────────────────────────────────────────────────────────
// GEOMETRY HELPERS
// ─────────────────────────────────────────────────────────────────────────

function offsetPoint(lat, lng, bearingDeg, distanceM) {
  const R = 6371000;
  const d = distanceM / R;
  const brg = (bearingDeg * Math.PI) / 180;
  const lat1 = (lat * Math.PI) / 180;
  const lng1 = (lng * Math.PI) / 180;
  const lat2 = Math.asin(
    Math.sin(lat1) * Math.cos(d) + Math.cos(lat1) * Math.sin(d) * Math.cos(brg)
  );
  const lng2 =
    lng1 +
    Math.atan2(
      Math.sin(brg) * Math.sin(d) * Math.cos(lat1),
      Math.cos(d) - Math.sin(lat1) * Math.sin(lat2)
    );
  return {
    lat: (lat2 * 180) / Math.PI,
    lng: (lng2 * 180) / Math.PI,
  };
}

function bearingBetween(latA, lngA, latB, lngB) {
  const toRad = (d) => (d * Math.PI) / 180;
  const y = Math.sin(toRad(lngB - lngA)) * Math.cos(toRad(latB));
  const x =
    Math.cos(toRad(latA)) * Math.sin(toRad(latB)) -
    Math.sin(toRad(latA)) * Math.cos(toRad(latB)) * Math.cos(toRad(lngB - lngA));
  const brg = (Math.atan2(y, x) * 180) / Math.PI;
  return (brg + 360) % 360;
}

function angleDiff(a, b) {
  return ((b - a + 540) % 360) - 180;
}

// ─────────────────────────────────────────────────────────────────────────
// STEP 8 — RALLY PATH GEOMETRY (NO OSRM)
// ─────────────────────────────────────────────────────────────────────────

async function getRallyPathGeometry(startLat, startLng, bearing, distance = 1000) {
  // Issue 4 fix: use actual road geometry from cache instead of a straight line
  const cache = await loadRoadCache();
  const nearby = cachedRoadsNear(cache, startLat, startLng, 60);
  const mainRoad = nearby.find((r) => isMainRoad(r.name, r.highway));

  if (mainRoad && mainRoad.geometry.length >= 2) {
    // Issue 2 fix: pick the nearest main road by actual distance, not JSON order
    const sorted = nearby
      .filter((r) => isMainRoad(r.name, r.highway))
      .sort((a, b) => {
        const da = Math.min(
          ...a.geometry.map(([lat, lng]) => distanceMeters(startLat, startLng, lat, lng))
        );
        const db = Math.min(
          ...b.geometry.map(([lat, lng]) => distanceMeters(startLat, startLng, lat, lng))
        );
        return da - db;
      });
    const bestRoad = sorted[0] || mainRoad;

    // Find the geometry node nearest to the click
    let nearestIdx = 0;
    let bestDist = Infinity;
    bestRoad.geometry.forEach(([lat, lng], i) => {
      const d = distanceMeters(startLat, startLng, lat, lng);
      if (d < bestDist) {
        bestDist = d;
        nearestIdx = i;
      }
    });

    // Issue 1 fix: check if the OSM geometry runs opposite to the rally
    // bearing. If so, reverse it so slice() always walks in the rally direction.
    const fwdNode = bestRoad.geometry[Math.min(nearestIdx + 1, bestRoad.geometry.length - 1)];
    const [nLat, nLng] = bestRoad.geometry[nearestIdx];
    const forwardBearing = bearingBetween(nLat, nLng, fwdNode[0], fwdNode[1]);
    const geometry = Math.abs(angleDiff(bearing, forwardBearing)) > 90
      ? [...bestRoad.geometry].reverse()
      : bestRoad.geometry;

    // After possible reversal, re-find the nearest index in the (possibly reversed) geometry
    let sliceNearestIdx = 0;
    let sliceBestDist = Infinity;
    geometry.forEach(([lat, lng], i) => {
      const d = distanceMeters(startLat, startLng, lat, lng);
      if (d < sliceBestDist) {
        sliceBestDist = d;
        sliceNearestIdx = i;
      }
    });

    // Accumulate real distances forward from the nearest node
    let endIdx = sliceNearestIdx;
    let travelled = 0;
    while (endIdx < geometry.length - 1 && travelled < distance) {
      const [lat1, lng1] = geometry[endIdx];
      const [lat2, lng2] = geometry[endIdx + 1];
      travelled += distanceMeters(lat1, lng1, lat2, lng2);
      endIdx++;
    }

    const coords = geometry
      .slice(sliceNearestIdx, endIdx + 1)
      .map(([lat, lng]) => [lng, lat]);

    const endPt = offsetPoint(startLat, startLng, bearing, distance);
    return { coords, end: endPt, steps: [], rallyRoadName: bestRoad.name };
  }

  // Fallback: straight-line waypoints every 50m if no road found in cache
  const coords = [];
  const step = 50;
  for (let d = 0; d <= distance; d += step) {
    const p = offsetPoint(startLat, startLng, bearing, d);
    coords.push([p.lng, p.lat]);
  }
  const end = offsetPoint(startLat, startLng, bearing, distance);
  return { coords, end, steps: [], rallyRoadName: null };
}

// ─────────────────────────────────────────────────────────────────────────
// STEP 6 — GET CROSSING ROADS (CACHE ONLY, NO OVERPASS)
// ─────────────────────────────────────────────────────────────────────────

async function getCrossingRoads(rallyPath, rallyRoadName) {
  const cache = await loadRoadCache();

  const found = [];

  for (const [lng, lat] of rallyPath) {
    const nearby = cachedRoadsNear(cache, lat, lng, 120);

    for (const road of nearby) {
      if (!road.name) continue;

      if (
        rallyRoadName &&
        road.name.toLowerCase() === rallyRoadName.toLowerCase()
      )
        continue;

      // Issue 3 fix: require at least one geometry node within 20m of the
      // rally path point — prevents parallel roads from being flagged as crossings
      const intersects = road.geometry.some(
        ([rLat, rLng]) => distanceMeters(lat, lng, rLat, rLng) <= 20
      );
      if (!intersects) continue;

      // Issue 1 fix: dedup against r.tags?.name, not r.name (r is Overpass-shaped)
      const already = found.some((r) => r.tags?.name === road.name);
      if (already) continue;

      found.push(cachedRoadToOverpassShape(road));
    }
  }

  return found;
}

// ─────────────────────────────────────────────────────────────────────────
// CROSSING POINT + BEARING HELPERS
// ─────────────────────────────────────────────────────────────────────────

function findCrossingPoint(rallyCoords, roadGeometry) {
  if (!roadGeometry?.length) return null;

  let minDist = Infinity;
  let closestPoint = null;
  let closestRallyIdx = 0;

  for (const roadNode of roadGeometry) {
    const roadLat = roadNode.lat;
    const roadLng = roadNode.lon;

    for (let i = 0; i < rallyCoords.length; i++) {
      const rallyPt = rallyCoords[i];
      // Problem 3 fix: use real meters instead of degree distance
      const dist = distanceMeters(roadLat, roadLng, rallyPt[1], rallyPt[0]);
      if (dist < minDist) {
        minDist = dist;
        closestPoint = { lat: roadLat, lng: roadLng };
        closestRallyIdx = i;
      }
    }
  }

  // Problem 3 fix: 25m threshold instead of the ~220m degree approximation
  if (minDist > 25) return null;
  return { point: closestPoint, rallyIdx: closestRallyIdx };
}

function rallyLocalBearing(rallyCoords, idx) {
  const lo = Math.max(0, idx - 2);
  const hi = Math.min(rallyCoords.length - 1, idx + 2);
  const a = rallyCoords[lo];
  const b = rallyCoords[hi];
  if (!a || !b || (a[0] === b[0] && a[1] === b[1])) return null;
  // rallyCoords are [lng, lat]
  return bearingBetween(a[1], a[0], b[1], b[0]);
}

function crossingRoadLocalBearing(roadGeometry, crossingPoint) {
  if (!roadGeometry || roadGeometry.length < 2) return null;

  let bestIdx = 0;
  let bestDist = Infinity;
  roadGeometry.forEach((n, i) => {
    const d = Math.hypot(n.lat - crossingPoint.lat, n.lon - crossingPoint.lng);
    if (d < bestDist) {
      bestDist = d;
      bestIdx = i;
    }
  });

  const lo = Math.max(0, bestIdx - 2);
  const hi = Math.min(roadGeometry.length - 1, bestIdx + 2);
  const a = roadGeometry[lo];
  const b = roadGeometry[hi];
  if (!a || !b) return null;
  return bearingBetween(a.lat, a.lon, b.lat, b.lon);
}

function geometryBasedSide(rallyCoords, rallyIdx, roadGeometry, crossingPoint) {
  const rallyBrg = rallyLocalBearing(rallyCoords, rallyIdx);
  const roadBrg = crossingRoadLocalBearing(roadGeometry, crossingPoint);

  if (rallyBrg == null || roadBrg == null) return "right";

  const diff = angleDiff(rallyBrg, roadBrg);
  return diff >= 0 ? "right" : "left";
}

// ─────────────────────────────────────────────────────────────────────────
// PICK LEFT / RIGHT FROM CANDIDATES
// ─────────────────────────────────────────────────────────────────────────

// Issue 3 fix: accept rallyBearing so left/right is computed relative to
// the rally's actual direction of travel, not a fixed west=left assumption.
function pickLeftRightFromCandidates(candidates, crossingPoint, blockedRoadName, rallyBearing) {
  const filtered = candidates.filter((el) => {
    const name = el.tags?.name || "";
    const hw = el.tags?.highway || "";
    if (!name || name === blockedRoadName) return false;
    return isMainRoad(name, hw);
  });

  if (filtered.length === 0) return { left: null, right: null };

  let bestLeft = null;
  let bestLeftDist = Infinity;
  let bestRight = null;
  let bestRightDist = Infinity;

  for (const way of filtered) {
    const geom = way.geometry || [];
    if (geom.length === 0) continue;

    let nearest = geom[0];
    let nearestDist = Infinity;
    for (const node of geom) {
      const d = distanceMeters(node.lat, node.lon, crossingPoint.lat, crossingPoint.lng);
      if (d < nearestDist) {
        nearestDist = d;
        nearest = node;
      }
    }

    const brg = bearingBetween(
      crossingPoint.lat,
      crossingPoint.lng,
      nearest.lat,
      nearest.lon
    );

    // Issue 3 fix: use rally bearing to determine true left vs right.
    // angleDiff > 0 means the candidate is to the RIGHT of the rally direction.
    const diff = rallyBearing != null
      ? angleDiff(rallyBearing, brg)
      : (brg > 180 ? -1 : 1); // fallback: west=left

    if (diff < 0 && nearestDist < bestLeftDist) {
      bestLeftDist = nearestDist;
      bestLeft = way.tags.name;
    } else if (diff >= 0 && nearestDist < bestRightDist) {
      bestRightDist = nearestDist;
      bestRight = way.tags.name;
    }
  }

  return { left: bestLeft, right: bestRight };
}

// ─────────────────────────────────────────────────────────────────────────
// STEP 7 — FIND PARALLEL ROADS (CACHE ONLY, NO OVERPASS)
// ─────────────────────────────────────────────────────────────────────────

async function findParallelRoads(crossingPoint, blockedRoadName, rallyBearing) {
  const cache = await loadRoadCache();

  // Issue 4 fix: tightened to 100m to avoid flyovers and cross-layout roads
  const nearby = cachedRoadsNear(cache, crossingPoint.lat, crossingPoint.lng, 100);

  const candidates = nearby
    .filter((r) => r.name && r.name !== blockedRoadName)
    .map(cachedRoadToOverpassShape);

  return pickLeftRightFromCandidates(candidates, crossingPoint, blockedRoadName, rallyBearing);
}

// ─────────────────────────────────────────────────────────────────────────
// BUILD DIVERSION INSTRUCTION
// ─────────────────────────────────────────────────────────────────────────

async function buildDiversionInstruction(rallyCoords, rallyIdx, road, crossingPoint) {
  const side = geometryBasedSide(rallyCoords, rallyIdx, road.geometry, crossingPoint);
  // Pass the rally's local bearing into findParallelRoads so pickLeftRight
  // uses direction-aware left/right instead of the fixed west=left heuristic
  const rallyBrg = rallyLocalBearing(rallyCoords, rallyIdx);
  const parallel = await findParallelRoads(crossingPoint, road.name, rallyBrg);

  const altRoad = side === "left" ? parallel.left : parallel.right;
  const fallbackAlt = side === "left" ? parallel.right : parallel.left;
  const chosenAlt = altRoad || fallbackAlt;
  const actualSide = altRoad
    ? side
    : fallbackAlt
    ? side === "left"
      ? "right"
      : "left"
    : side;

  if (chosenAlt) {
    return {
      direction: actualSide,
      altRoad: chosenAlt,
      text: `Turn ${actualSide} before ${road.name} — use ${chosenAlt} instead`,
    };
  }

  return {
    direction: side,
    altRoad: null,
    text: `Turn ${side} before ${road.name} (no named alternate route found nearby)`,
  };
}

// ─────────────────────────────────────────────────────────────────────────
// MAIN EXPORT
// ─────────────────────────────────────────────────────────────────────────

/**
 * analyzeRallyRoute(startLat, startLng, bearingDeg, distanceM)
 *
 * Returns:
 * {
 *   rallyPath: [[lng, lat], ...],
 *   rallyRoadName: string | null,
 *   crossingRoads: [
 *     {
 *       name: string,
 *       highway: string,
 *       crossingPoint: { lat, lng },
 *       diversionDirection: string,
 *       diversionSide: "left" | "right",
 *       diversionRoad: string | null,
 *       geometry: [[lat, lng], ...],
 *     },
 *     ...
 *   ],
 *   summary: string,
 * }
 */
export async function analyzeRallyRoute(startLat, startLng, bearingDeg, distanceM = 800) {
  const pathResult = await getRallyPathGeometry(startLat, startLng, bearingDeg, distanceM);
  if (!pathResult) {
    return {
      rallyPath: null,
      rallyRoadName: null,
      crossingRoads: [],
      summary: "Could not compute rally route.",
    };
  }

  const { coords } = pathResult;

  // Issue 2 fix: prefer a main road over whatever is first in the nearby list
  let rallyRoadName = pathResult.rallyRoadName || null;
  if (!rallyRoadName) {
    try {
      const cache = await loadRoadCache();
      const nearby = cachedRoadsNear(cache, startLat, startLng, 100);

      // Issue 5 fix: graceful fallback when cache covers nothing near this point
      if (nearby.length === 0) {
        return {
          rallyPath: coords,
          rallyRoadName: "Unnamed Road",
          crossingRoads: [],
          summary: "No cached roads found nearby. The rally path has been plotted but no intersections could be determined.",
        };
      }

      const mainRoad = nearby.find((r) => isMainRoad(r.name, r.highway));
      rallyRoadName = mainRoad?.name || nearby[0]?.name || null;
    } catch (_) {}
  }

  const crossingWays = await getCrossingRoads(coords, rallyRoadName);

  // PASS 1 — geometry only, no network
  const seen = new Set();
  const candidates = [];

  for (const way of crossingWays) {
    const name = way.tags?.name;
    if (!name || seen.has(name)) continue;
    seen.add(name);

    const geometry = way.geometry || [];
    const found = findCrossingPoint(coords, geometry);
    if (!found) continue;
    const { point: crossingPoint, rallyIdx } = found;

    const side = geometryBasedSide(coords, rallyIdx, geometry, crossingPoint);

    candidates.push({
      name,
      highway: way.tags?.highway,
      crossingPoint,
      rallyIdx,
      geometry,
      side,
      // Issue 2 fix: use real metres, not Manhattan degrees
      distFromStart: distanceMeters(startLat, startLng, crossingPoint.lat, crossingPoint.lng),
    });
  }

  candidates.sort((a, b) => a.distFromStart - b.distFromStart);

  // PASS 2 — parallel road lookup (all from cache, instant)
  const crossingRoads = [];

  for (const c of candidates) {
    const instruction = await buildDiversionInstruction(
      coords,
      c.rallyIdx,
      { name: c.name, geometry: c.geometry },
      c.crossingPoint
    );

    crossingRoads.push({
      name: c.name,
      highway: c.highway,
      crossingPoint: c.crossingPoint,
      diversionDirection: instruction.text,
      diversionSide: instruction.direction,
      diversionRoad: instruction.altRoad,
      geometry: c.geometry.map((n) => [n.lat, n.lon]),
    });
  }

  const summary =
    crossingRoads.length > 0
      ? `Rally moving along ${rallyRoadName || "route"}. ${crossingRoads.length} main road(s) affected: ${crossingRoads.map((r) => r.name).join(", ")}.`
      : `Rally moving along ${rallyRoadName || "route"}. No major road intersections found along this path.`;

  return {
    rallyPath: coords,
    rallyRoadName,
    crossingRoads,
    summary,
  };
}
import { useEffect, useRef, useState, useCallback } from 'react';
import { colors, typography, cards, buttons } from '../styles/globals';

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const EVENT_TYPES = [
  { value: 'procession', label: 'Procession' },
  { value: 'public_event', label: 'Public Event' },
  { value: 'vip_movement', label: 'VIP Movement' },
  { value: 'construction', label: 'Construction' },
  { value: 'protest', label: 'Protest' },
];

const CAUSE_COLORS = {
  vehicle_breakdown: '#2563EB',
  accident: '#DC2626',
  water_logging: '#0891B2',
  construction: '#D97706',
  public_event: '#7C3AED',
  procession: '#7C3AED',
  vip_movement: '#059669',
  tree_fall: '#16A34A',
  pot_holes: '#D97706',
  protest: '#DC2626',
  others: '#6B7280',
};

const SEVERITY_COLORS = {
  High: '#DC2626',
  Low: '#059669',
  unknown: '#6B7280',
};

// ── Step indicator ────────────────────────────────────────────────────────────
function StepDot({ num, label, active, done }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
      <div style={{
        width: '28px', height: '28px', borderRadius: '50%', display: 'flex',
        alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 600,
        backgroundColor: done ? '#059669' : active ? '#2563EB' : 'var(--color-gray-bg)',
        color: done || active ? '#fff' : 'var(--color-text-tertiary)',
        border: `2px solid ${done ? '#059669' : active ? '#2563EB' : 'var(--color-border)'}`,
        transition: 'all 300ms ease',
      }}>
        {done ? '✓' : num}
      </div>
      <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.06em',
        color: active ? '#2563EB' : 'var(--color-text-tertiary)', fontWeight: 600, whiteSpace: 'nowrap' }}>
        {label}
      </span>
    </div>
  );
}

function StepLine({ done }) {
  return (
    <div style={{ flex: 1, height: '2px', marginBottom: '20px',
      backgroundColor: done ? '#059669' : 'var(--color-border)', transition: 'background-color 300ms ease' }} />
  );
}

// ── Confidence badge ──────────────────────────────────────────────────────────
function ConfidenceBadge({ tier }) {
  const map = {
    strong: { color: '#059669', bg: '#ECFDF5', label: 'Strong precedent' },
    moderate: { color: '#D97706', bg: '#FFFBEB', label: 'Moderate precedent' },
    thin: { color: '#DC2626', bg: '#FEF2F2', label: 'Thin precedent' },
    no_precedent: { color: '#6B7280', bg: 'var(--color-gray-bg)', label: 'No precedent' },
  };
  const c = map[tier] || map.no_precedent;
  return (
    <span style={{ fontSize: '11px', fontWeight: 600, padding: '2px 8px', borderRadius: '99px',
      backgroundColor: c.bg, color: c.color, border: `1px solid ${c.color}30` }}>
      {c.label}
    </span>
  );
}

const COMPASS_DIRS = [
  { label: 'N',  bearing: 0,   top: '2px',   left: '50%',  transform: 'translateX(-50%)' },
  { label: 'NE', bearing: 45,  top: '14px',  left: '72%',  transform: '' },
  { label: 'E',  bearing: 90,  top: '50%',   left: '85%',  transform: 'translateY(-50%)' },
  { label: 'SE', bearing: 135, top: '72%',   left: '72%',  transform: '' },
  { label: 'S',  bearing: 180, top: '85%',   left: '50%',  transform: 'translateX(-50%)' },
  { label: 'SW', bearing: 225, top: '72%',   left: '14%',  transform: '' },
  { label: 'W',  bearing: 270, top: '50%',   left: '2px',  transform: 'translateY(-50%)' },
  { label: 'NW', bearing: 315, top: '14px',  left: '14%',  transform: '' },
];
 
function CompassPicker({ value, onChange }) {
  return (
    <div style={{ position: 'relative', width: '120px', height: '120px', margin: '0 auto' }}>
      {/* Outer ring */}
      <div style={{
        position: 'absolute', inset: '10px', borderRadius: '50%',
        border: '1px solid var(--color-border)', backgroundColor: 'var(--color-gray-bg)',
      }} />
      {/* Center dot */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '6px', height: '6px', borderRadius: '50%',
        backgroundColor: 'var(--color-text-tertiary)',
      }} />
      {/* Arrow pointing rally direction */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        width: '2px', height: '34px',
        backgroundColor: '#DC2626',
        transformOrigin: 'bottom center',
        transform: `translateX(-50%) rotate(${value}deg)`,
        transition: 'transform 200ms ease',
        bottom: '50%', marginTop: '-34px',
      }} />
      {/* Direction buttons */}
      {COMPASS_DIRS.map(({ label, bearing, top, left, transform }) => (
        <button
          key={label}
          onClick={() => onChange(bearing)}
          style={{
            position: 'absolute', top, left, transform,
            width: '24px', height: '24px', borderRadius: '50%',
            border: `1px solid ${value === bearing ? '#DC2626' : 'var(--color-border)'}`,
            backgroundColor: value === bearing ? '#DC2626' : 'var(--color-card-bg)',
            color: value === bearing ? '#fff' : 'var(--color-text-secondary)',
            fontSize: '9px', fontWeight: 700, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 150ms ease', zIndex: 2,
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
 
// ── ADD 2: DirectionalResultPanel component (add before SimulationPage) ──────
 
const QUADRANT_COLORS = {
  head_on:     '#DC2626',   // Red - most urgent
  tail_on:     '#D97706',   // Amber - moderate
  cross_left:  '#2563EB',   // Blue
  cross_right: '#7C3AED',   // Purple
};
 
const QUADRANT_ICONS = {
  head_on:     '⚠️',
  tail_on:     '🔁',
  cross_left:  '↰',
  cross_right: '↱',
};
 
function DirectionalResultPanel({ result }) {
  if (!result) return null;
  const { rally_direction_label, approach_groups, summary, classification, resolution_estimate } = result;
 
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
 
      {/* Summary banner */}
      <div style={{
        padding: '12px 14px', borderRadius: '6px',
        backgroundColor: '#FEF2F2', border: '1px solid #DC262630',
        fontSize: '13px', lineHeight: '1.6', color: '#DC2626', fontWeight: 500,
      }}>
        🚨 {summary}
      </div>
 
      {/* Classification */}
      {classification && (
        <div style={{ ...cardStyle }}>
          <div style={labelStyle}>Classification</div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px' }}>
            <span style={tagStyle(CAUSE_COLORS[classification.event_cause] || '#6B7280')}>
              {classification.event_cause?.replace(/_/g, ' ')}
            </span>
            <span style={tagStyle(SEVERITY_COLORS[classification.severity])}>
              {classification.severity} severity
            </span>
            <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', alignSelf: 'center' }}>
              {Math.round((classification.cause_confidence || 0) * 100)}% confidence
            </span>
          </div>
        </div>
      )}
 
      {/* Per-direction diversion cards */}
      <div style={{ ...cardStyle }}>
        <div style={labelStyle}>Directional traffic plan — Rally moving {rally_direction_label}</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
          {Object.entries(approach_groups || {}).map(([quadrant, group]) => {
            const div = group.diversion;
            const color = QUADRANT_COLORS[quadrant];
            return (
              <div key={quadrant} style={{
                padding: '10px 12px', borderRadius: '6px',
                border: `1px solid ${color}30`,
                backgroundColor: `${color}08`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '14px' }}>{QUADRANT_ICONS[quadrant]}</span>
                    <span style={{ fontSize: '12px', fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      {quadrant.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {div && (
                    <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
                      {Math.round(div.distance_from_incident_m)}m away
                    </span>
                  )}
                </div>
 
                <div style={{ fontSize: '11px', color, marginTop: '4px', fontWeight: 500 }}>
                  {group.instruction}
                </div>
 
                {group.approach_corridors?.length > 0 && (
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    Affected: {group.approach_corridors.join(' · ')}
                  </div>
                )}
 
                {div ? (
                  <div style={{
                    marginTop: '6px', padding: '6px 10px', borderRadius: '4px',
                    backgroundColor: '#F0FDF4', border: '1px solid #05966930',
                    display: 'flex', alignItems: 'center', gap: '6px',
                  }}>
                    <span style={{ color: '#059669', fontSize: '12px' }}>✓ Divert via</span>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#059669' }}>
                      {div.corridor}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginLeft: 'auto' }}>
                      {div.reason}
                    </span>
                  </div>
                ) : (
                  <div style={{ marginTop: '6px', fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
                    No clear diversion found for this direction
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
 
      {/* Resolution time */}
      {resolution_estimate?.predicted_minutes && (
        <div style={cardStyle}>
          <div style={labelStyle}>Predicted clearance</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-text-primary)', marginTop: '4px' }}>
            ~{Math.round(resolution_estimate.predicted_minutes)} min
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
            Range: {Math.round(resolution_estimate.confidence_band?.[0])}–
            {Math.round(resolution_estimate.confidence_band?.[1])} min
          </div>
        </div>
      )}
    </div>
  );
}
 
// Shared style helpers for DirectionalResultPanel
const cardStyle = {
  backgroundColor: 'var(--color-card-bg)',
  border: '1px solid var(--color-border)',
  borderRadius: '8px', padding: '14px 16px',
};
const labelStyle = {
  fontFamily: "'Inter', sans-serif", fontSize: '11px',
  textTransform: 'uppercase', letterSpacing: '0.08em',
  color: 'var(--color-text-secondary)', fontWeight: '600',
};
const tagStyle = (color) => ({
  fontSize: '13px', fontWeight: 600, padding: '3px 10px', borderRadius: '99px',
  backgroundColor: `${color}15`, color,
  border: `1px solid ${color}30`,
});

// ── Main component ────────────────────────────────────────────────────────────
export default function SimulationPage() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);

  // Form state
  const [mode, setMode] = useState('unplanned'); // 'unplanned' | 'planned'
  const [description, setDescription] = useState('');
  const [eventType, setEventType] = useState('public_event');
  const [clickStep, setClickStep] = useState(0); // 0=idle, 1=waiting start, 2=waiting end
  const [startPoint, setStartPoint] = useState(null);   // { lat, lng, address }
  const [endPoint, setEndPoint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [corridors, setCorridors] = useState([]);
  const [rallyBearing, setRallyBearing] = useState(0);
  const [directionalResult, setDirectionalResult] = useState(null);

  // Derived step for the step indicator
  const step = result ? 3 : clickStep === 0 && !startPoint ? 0 : startPoint && !result ? 2 : 1;

  // ── Map init ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainer.current || mapRef.current || !window.maplibregl) return;

    const map = new window.maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap',
          }
        },
        layers: [{ id: 'osm', type: 'raster', source: 'osm', minzoom: 0, maxzoom: 19 }]
      },
      center: [77.59, 12.97],
      zoom: 11,
    });

    mapRef.current = map;

    // Load corridor geometry once
    map.on('load', async () => {
      try {
        const res = await fetch(`${API_BASE}/diversion/corridors`);
        const data = await res.json();
        setCorridors(data.corridors || []);

        // Draw corridor polylines as faint overlay
        const features = (data.corridors || [])
          .filter(c => c.points && c.points.length > 1)
          .map(c => ({
            type: 'Feature',
            properties: { name: c.name, count: c.n_historical_events },
            geometry: {
              type: 'LineString',
              coordinates: c.points.map(p => [p[1], p[0]]) // [lng, lat]
            }
          }));

        map.addSource('corridors', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features }
        });

        map.addLayer({
          id: 'corridors-line',
          type: 'line',
          source: 'corridors',
          paint: {
            'line-color': '#94A3B8',
            'line-width': 2,
            'line-opacity': 0.35,
            'line-dasharray': [3, 3],
          }
        });

      } catch (e) {
        console.warn('Could not load corridor geometry:', e);
      }
    });

    return () => { map.remove(); mapRef.current = null; };
  }, []);

  // ── Map click handler ──────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const onClick = async (e) => {
      if (clickStep === 0) return;

      const { lat, lng } = e.lngLat;

      // Reverse geocode with Nominatim (free, no API key)
      let address = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`
        );
        const data = await res.json();
        address = data.display_name?.split(',').slice(0, 3).join(', ') || address;
      } catch (_) {}

      const point = { lat, lng, address };

      if (clickStep === 1 || mode === 'unplanned') {
        setStartPoint(point);
        placeMarker(lat, lng, 'start');
        if (mode === 'unplanned') {
          setClickStep(0);
        } else {
          setClickStep(2);
        }
      } else if (clickStep === 2) {
        setEndPoint(point);
        placeMarker(lat, lng, 'end');
        setClickStep(0);
      }
    };

    map.on('click', onClick);
    return () => map.off('click', onClick);
  }, [clickStep, mode]);

  // ── Cursor style when in click mode ──────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.getCanvas().style.cursor = clickStep > 0 ? 'crosshair' : '';
  }, [clickStep]);

  // ── Marker helpers ────────────────────────────────────────────────────────
  const placeMarker = useCallback((lat, lng, type) => {
    const map = mapRef.current;
    if (!map) return;

    const el = document.createElement('div');
    const isStart = type === 'start';
    const isEnd = type === 'end';
    const isDiversion = type === 'diversion';
    const isBarricade = type === 'barricade';
    const isRallyTip = type === 'rally-tip';

    if (isRallyTip) {
      el.style.cssText = `
        font-size: 20px; cursor: default; line-height: 1;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
      `;
      el.innerHTML = '🚨';
      const marker = new window.maplibregl.Marker({ element: el, anchor: 'bottom' })
        .setLngLat([lng, lat])
        .addTo(map);
      markersRef.current.push(marker);
      return;
    }

    el.style.cssText = `
      width: ${isDiversion ? '14px' : isBarricade ? '20px' : '16px'};
      height: ${isDiversion ? '14px' : isBarricade ? '20px' : '16px'};
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: ${isBarricade ? '12px' : '0px'};
      background-color: ${
        isStart ? '#F97316' :
        isEnd ? '#F97316' :
        isDiversion ? '#059669' :
        isBarricade ? '#DC2626' : '#6B7280'
      };
      border: 2px solid white;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      cursor: default;
      transition: transform 150ms ease;
    `;
    if (isBarricade) el.innerHTML = '🚧';
    if (isBarricade) el.style.background = 'none';
    if (isBarricade) el.style.border = 'none';
    if (isBarricade) el.style.fontSize = '18px';

    const marker = new window.maplibregl.Marker({ element: el })
      .setLngLat([lng, lat])
      .addTo(map);

    markersRef.current.push(marker);
  }, []);


  const clearMapState = useCallback(() => {
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    const map = mapRef.current;
    if (!map) return;

    // Remove all diversion layers (including directional ones)
    const layerIds = [
      'event-path', 'impact-circle', 'diversion-arrow',
      'rally-route', 'rally-route-border',
      'dir-head_on', 'dir-tail_on', 'dir-cross_left', 'dir-cross_right',
      'dir-head_on-border', 'dir-tail_on-border', 'dir-cross_left-border', 'dir-cross_right-border',
      'dir-head_on-approach', 'dir-tail_on-approach', 'dir-cross_left-approach', 'dir-cross_right-approach',
      'dir-head_on-approach-border', 'dir-tail_on-approach-border', 'dir-cross_left-approach-border', 'dir-cross_right-approach-border',
    ];
    layerIds.forEach(id => {
      if (map.getLayer(id)) map.removeLayer(id);
      if (map.getSource(id)) map.removeSource(id);
    });
  }, []);

  // ── OSRM route fetcher (road-following) ───────────────────────────────────
  const fetchOsrmRoute = useCallback(async (fromLat, fromLng, toLat, toLng) => {
    try {
      const url = `https://router.project-osrm.org/route/v1/driving/${fromLng},${fromLat};${toLng},${toLat}?overview=full&geometries=geojson`;
      const res = await fetch(url);
      if (!res.ok) return null;
      const json = await res.json();
      if (json.code !== 'Ok' || !json.routes?.[0]) return null;
      return json.routes[0].geometry.coordinates; // [[lng, lat], ...]
    } catch {
      return null;
    }
  }, []);

  // ── Add or update a GeoJSON line layer ────────────────────────────────────
  const upsertLineLayer = useCallback((map, id, coords, color, width, dasharray, opacity) => {
    const geojson = {
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: coords }
    };
    if (map.getSource(id)) {
      map.getSource(id).setData(geojson);
    } else {
      map.addSource(id, { type: 'geojson', data: geojson });
      // White border for readability
      map.addLayer({
        id: `${id}-border`,
        type: 'line',
        source: id,
        paint: { 'line-color': '#ffffff', 'line-width': width + 3, 'line-opacity': opacity * 0.6 }
      });
      map.addLayer({
        id,
        type: 'line',
        source: id,
        paint: {
          'line-color': color,
          'line-width': width,
          'line-opacity': opacity,
          ...(dasharray ? { 'line-dasharray': dasharray } : {})
        }
      });
    }
  }, []);

  // ── Place a quadrant diversion marker with icon ───────────────────────────
  const placeDiversionPin = useCallback((lat, lng, color, icon, label) => {
    const map = mapRef.current;
    if (!map) return;
    const el = document.createElement('div');
    el.style.cssText = `
      width: 30px; height: 30px; border-radius: 50%;
      background-color: ${color};
      border: 3px solid white;
      box-shadow: 0 3px 10px rgba(0,0,0,0.4);
      display: flex; align-items: center; justify-content: center;
      font-size: 14px; cursor: default;
      position: relative;
    `;
    el.innerHTML = icon;
    el.title = label;
    // Small label bubble below
    const bubble = document.createElement('div');
    bubble.style.cssText = `
      position: absolute; bottom: -22px; left: 50%;
      transform: translateX(-50%);
      background: ${color}; color: white;
      font-size: 9px; font-weight: 700;
      padding: 2px 5px; border-radius: 3px;
      white-space: nowrap;
      font-family: Inter, sans-serif;
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    `;
    bubble.textContent = label;
    el.appendChild(bubble);
    const marker = new window.maplibregl.Marker({ element: el })
      .setLngLat([lng, lat])
      .addTo(map);
    markersRef.current.push(marker);
  }, []);

  // ── Draw directional result on map ────────────────────────────────────────
  const drawDirectionalResult = useCallback(async (data, rallyBearing, incidentLat, incidentLng) => {
    const map = mapRef.current;
    if (!map) return;

    placeMarker(incidentLat, incidentLng, 'barricade');

    // Small impact zone circle
    const circlePts = [];
    const rDeg = 220 / 111139;
    for (let i = 0; i <= 48; i++) {
      const a = (i * Math.PI * 2) / 48;
      circlePts.push([incidentLng + rDeg * Math.cos(a), incidentLat + rDeg * 0.9 * Math.sin(a)]);
    }
    if (map.getSource('impact-circle')) {
      map.getSource('impact-circle').setData({ type: 'Feature', geometry: { type: 'Polygon', coordinates: [circlePts] } });
    } else {
      map.addSource('impact-circle', { type: 'geojson', data: { type: 'Feature', geometry: { type: 'Polygon', coordinates: [circlePts] } } });
      map.addLayer({ id: 'impact-circle', type: 'fill', source: 'impact-circle', paint: { 'fill-color': '#F97316', 'fill-opacity': 0.15 } });
    }

    // ── Helpers ──────────────────────────────────────────────────────────────
    const toRad = d => (d * Math.PI) / 180;
    const off = (lat, lng, brg, distM) => {
      const d = distM / 111139;
      return [lat + d * Math.cos(toRad(brg)), lng + d * Math.sin(toRad(brg))];
    };
    const osrm = async (...pts) => {
      try {
        const wps = pts.map(p => `${p[1]},${p[0]}`).join(';');
        const j = await (await fetch(
          `https://router.project-osrm.org/route/v1/driving/${wps}?overview=full&geometries=geojson`
        )).json();
        return (j.code === 'Ok' && j.routes?.[0]) ? j.routes[0].geometry.coordinates : null;
      } catch { return null; }
    };

    // Bearings relative to rally direction
    const F = rallyBearing;         // Forward  (where rally travels)
    const B = (F + 180) % 360;     // Backward (behind rally)
    const R = (F + 90)  % 360;     // Right of rally path
    const L = (F + 270) % 360;     // Left of rally path


    // ── Rally: BLACK DASHED line, 650m forward ───────────────────────────────
    const rallyEnd = off(incidentLat, incidentLng, F, 650);
    const rallyCrd = await osrm([incidentLat, incidentLng], rallyEnd);
    if (rallyCrd) {
      upsertLineLayer(map, 'rally-route', rallyCrd, '#111827', 5, [9, 6], 0.85);
      const tip = rallyCrd[rallyCrd.length - 1];
      placeMarker(tip[1], tip[0], 'rally-tip');
    }

    const allPts = [[incidentLat, incidentLng]];

    // Calculate interception points for diversions
    const D = 380;   // intercept distance from incident (metres)

    // ── HEAD-ON (red): comes from FORWARD ────────────
    {
      const A = off(incidentLat, incidentLng, F, D);       // intercept ahead
      placeDiversionPin(A[0], A[1], '#DC2626', '⚠️', 'Head-on');
      allPts.push(A);
    }

    // ── TAIL-ON (amber): comes from BACKWARD ──────────
    {
      const A = off(incidentLat, incidentLng, B, D);       // intercept behind
      placeDiversionPin(A[0], A[1], '#D97706', '🔁', 'Tail-on');
      allPts.push(A);
    }

    // ── CROSS-LEFT (blue): comes from LEFT ──────
    {
      const A = off(incidentLat, incidentLng, L, D);       // intercept on left
      placeDiversionPin(A[0], A[1], '#2563EB', '↰', 'Cross L');
      allPts.push(A);
    }

    // ── CROSS-RIGHT (purple): comes from RIGHT ──
    {
      const A = off(incidentLat, incidentLng, R, D);       // intercept on right
      placeDiversionPin(A[0], A[1], '#7C3AED', '↱', 'Cross R');
      allPts.push(A);
    }


    // Fit map tightly around all key points
    const lats = allPts.map(p => p[0]);
    const lngs = allPts.map(p => p[1]);
    map.fitBounds(
      [[Math.min(...lngs) - 0.012, Math.min(...lats) - 0.012],
       [Math.max(...lngs) + 0.012, Math.max(...lats) + 0.012]],
      { padding: 60, duration: 900 }
    );
  }, [placeMarker, upsertLineLayer, placeDiversionPin]);




  // ── Draw result on map (planned mode) ────────────────────────────────────
  const drawResult = useCallback((data, isPlanned) => {
    const map = mapRef.current;
    if (!map) return;

    // Barricade at incident/start point
    placeMarker(data.barricade_point[0], data.barricade_point[1], 'barricade');

    // Green markers at diversion corridor centroids
    (data.diversions || []).forEach(d => {
      if (d.centroid) placeMarker(d.centroid[0], d.centroid[1], 'diversion');
    });

    // Impact circle
    const circlePts = [];
    const cx = data.barricade_point[1];
    const cy = data.barricade_point[0];
    const rDeg = (data.impact_radius_m || 300) / 111139;
    for (let i = 0; i <= 64; i++) {
      const a = (i * Math.PI * 2) / 64;
      circlePts.push([cx + rDeg * Math.cos(a), cy + rDeg * 0.9 * Math.sin(a)]);
    }
    if (map.getSource('impact-circle')) {
      map.getSource('impact-circle').setData({ type: 'Feature', geometry: { type: 'Polygon', coordinates: [circlePts] } });
    } else {
      map.addSource('impact-circle', { type: 'geojson', data: { type: 'Feature', geometry: { type: 'Polygon', coordinates: [circlePts] } } });
      map.addLayer({ id: 'impact-circle', type: 'fill', source: 'impact-circle', paint: { 'fill-color': '#F97316', 'fill-opacity': 0.15 } });
    }

    // Blue polyline for planned event path
    if (isPlanned && data.event_path && data.event_path.length >= 2) {
      const coords = data.event_path.map(p => [p[1], p[0]]);
      if (map.getSource('event-path')) {
        map.getSource('event-path').setData({ type: 'Feature', geometry: { type: 'LineString', coordinates: coords } });
      } else {
        map.addSource('event-path', { type: 'geojson', data: { type: 'Feature', geometry: { type: 'LineString', coordinates: coords } } });
        map.addLayer({ id: 'event-path', type: 'line', source: 'event-path', paint: { 'line-color': '#2563EB', 'line-width': 4, 'line-opacity': 0.85 } });
      }
    }

    // Dashed arrows to diversion centroids
    if (data.diversions?.length > 0) {
      const arrowCoords = data.diversions.filter(d => d.centroid).map(d => [
        [data.barricade_point[1], data.barricade_point[0]],
        [d.centroid[1], d.centroid[0]]
      ]);
      if (arrowCoords.length > 0) {
        const geojson = { type: 'Feature', geometry: { type: 'MultiLineString', coordinates: arrowCoords } };
        if (map.getSource('diversion-arrow')) {
          map.getSource('diversion-arrow').setData(geojson);
        } else {
          map.addSource('diversion-arrow', { type: 'geojson', data: geojson });
          map.addLayer({ id: 'diversion-arrow', type: 'line', source: 'diversion-arrow',
            paint: { 'line-color': '#059669', 'line-width': 3, 'line-dasharray': [6, 3], 'line-opacity': 0.9 } });
        }
      }
    }

    // Fit to all points
    const allPoints = [data.barricade_point, ...(data.diversions || []).map(d => d.centroid).filter(Boolean)];
    if (allPoints.length > 1) {
      const lats = allPoints.map(p => p[0]);
      const lngs = allPoints.map(p => p[1]);
      map.fitBounds(
        [[Math.min(...lngs) - 0.01, Math.min(...lats) - 0.01], [Math.max(...lngs) + 0.01, Math.max(...lats) + 0.01]],
        { padding: 60, duration: 800 }
      );
    }
  }, [placeMarker]);

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!startPoint) return;
    if (!description.trim() && mode === 'unplanned') {
      setError('Please describe the event or incident.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setDirectionalResult(null);

    try {
      if (mode === 'unplanned') {
        const res = await fetch(`${API_BASE}/diversion/directional`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            incident_lat: startPoint.lat,
            incident_lng: startPoint.lng,
            rally_bearing: rallyBearing,
            description: description,
          }),
        });
        if (!res.ok) throw new Error(`Server error ${res.status}`);
        const data = await res.json();
        setDirectionalResult(data);
        await drawDirectionalResult(data, rallyBearing, startPoint.lat, startPoint.lng);
        return;
      }

      // Planned event
      const endpoint = `${API_BASE}/diversion/planned`;
      const body = {
        event_type: eventType,
        description,
        start_lat: startPoint.lat,
        start_lng: startPoint.lng,
        ...(endPoint ? { end_lat: endPoint.lat, end_lng: endPoint.lng } : {}),
      };
      const res = await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setResult(data);
      drawResult(data, true);

    } catch (e) {
      setError(e.message || 'Request failed.');
    } finally {
      setLoading(false);
    }
  };


  // ── Reset ─────────────────────────────────────────────────────────────────
  const handleReset = () => {
    clearMapState();
    setStartPoint(null);
    setEndPoint(null);
    setResult(null);
    setDirectionalResult(null);
    setError(null);
    setClickStep(0);
    setDescription('');
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ ...typography.header, margin: 0, fontSize: '16px' }}>Traffic Diversion Simulator</h1>
          <p style={{ ...typography.subtitle, margin: 0, marginTop: '2px' }}>
            Simulate planned or unplanned events · See recommended diversion in real time
          </p>
        </div>
        <button onClick={handleReset} style={{ ...buttons.secondary, padding: '6px 14px', fontSize: '12px' }}>
          Reset
        </button>
      </div>

      {/* Step indicator */}
      <div style={{ ...cards.base, padding: '16px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <StepDot num={1} label="Choose mode" active={step === 0} done={step > 0} />
          <StepLine done={step > 0} />
          <StepDot num={2} label={mode === 'unplanned' ? 'Pin incident' : 'Pin route'} active={step === 1} done={step > 1} />
          <StepLine done={step > 1} />
          <StepDot num={3} label="Describe & analyse" active={step === 2} done={step > 2} />
          <StepLine done={step > 2} />
          <StepDot num={4} label="View diversion" active={step === 3} done={false} />
        </div>
      </div>

      {/* Main layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '16px', alignItems: 'start' }}>

        {/* Left Column (Map & Results) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Map */}
          <div style={{ position: 'relative' }}>
            <div style={{
              ...cards.base, padding: 0, overflow: 'hidden',
              height: '580px', position: 'relative',
            }}>
              <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

              {/* Map legend */}
              <div style={{
                position: 'absolute', bottom: '12px', left: '12px', zIndex: 10,
                ...cards.base, padding: '10px 14px', fontSize: '11px',
                display: 'flex', flexDirection: 'column', gap: '6px', minWidth: '180px',
              }}>
                <span style={{ ...typography.label, fontSize: '10px', marginBottom: '2px' }}>Legend</span>
                {(directionalResult ? [
                  { color: '#F97316', emoji: '🚧', label: 'Barricade / Incident' },
                  { color: '#111827', emoji: '━', label: 'Rally route (black)' },
                  { color: '#DC2626', emoji: '━', label: 'Head-on diversion' },
                  { color: '#D97706', emoji: '━', label: 'Tail-on diversion' },
                  { color: '#2563EB', emoji: '━', label: 'Cross-left diversion' },
                  { color: '#7C3AED', emoji: '━', label: 'Cross-right diversion' },
                ] : [
                  { color: '#F97316', emoji: '🚧', label: 'Barricade / Incident' },
                  { color: '#059669', emoji: '●', label: 'Diversion corridor' },
                  { color: '#2563EB', emoji: '—', label: 'Event path (planned)' },
                  { color: '#94A3B8', emoji: '- -', label: 'Corridors (overlay)' },
                ]).map(({ color, emoji, label }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color, fontSize: '14px', fontWeight: 800, width: '18px', textAlign: 'center', lineHeight: 1 }}>{emoji}</span>
                    <span style={{ color: 'var(--color-text-secondary)', fontSize: '11px' }}>{label}</span>
                  </div>
                ))}
              </div>

              {/* Click instruction overlay */}
              {clickStep > 0 && (
                <div style={{
                  position: 'absolute', top: '12px', left: '50%', transform: 'translateX(-50%)',
                  zIndex: 20, backgroundColor: '#2563EB', color: '#fff',
                  padding: '8px 16px', borderRadius: '99px', fontSize: '13px', fontWeight: 500,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)', pointerEvents: 'none',
                }}>
                  {clickStep === 1
                    ? mode === 'unplanned' ? '📍 Click where the incident occurred' : '📍 Click the event start point'
                    : '📍 Click the event end point (or skip below)'}
                </div>
              )}
            </div>
          </div>

          {/* === MOVED RESULTS SECTION === */}
          {directionalResult && (
            <DirectionalResultPanel result={directionalResult} />
          )}

          {/* Result card */}
          {result && !directionalResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {/* Classification */}
              <div style={cards.base}>
                <div style={{ ...typography.label, marginBottom: '8px' }}>Classification</div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{
                    fontSize: '13px', fontWeight: 600, padding: '3px 10px', borderRadius: '99px',
                    backgroundColor: `${CAUSE_COLORS[result.classification?.event_cause] || '#6B7280'}15`,
                    color: CAUSE_COLORS[result.classification?.event_cause] || '#6B7280',
                    border: `1px solid ${CAUSE_COLORS[result.classification?.event_cause] || '#6B7280'}30`,
                  }}>
                    {result.classification?.event_cause?.replace(/_/g, ' ')}
                  </span>
                  <span style={{
                    fontSize: '12px', fontWeight: 600, padding: '3px 10px', borderRadius: '99px',
                    backgroundColor: `${SEVERITY_COLORS[result.classification?.severity]}15`,
                    color: SEVERITY_COLORS[result.classification?.severity],
                  }}>
                    {result.classification?.severity} severity
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
                    {Math.round((result.classification?.cause_confidence || 0) * 100)}% confidence
                  </span>
                </div>
              </div>

              {/* Affected corridor */}
              <div style={cards.base}>
                <div style={{ ...typography.label, marginBottom: '6px' }}>Affected corridor</div>
                <div style={{ ...typography.value, fontSize: '14px' }}>
                  {result.affected_corridor || result.start_corridor || 'Not identified'}
                </div>
                {result.start_corridor && result.end_corridor && result.end_corridor !== result.start_corridor && (
                  <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    → {result.end_corridor}
                  </div>
                )}
              </div>

              {/* Diversion options */}
              {result.diversions?.length > 0 && (
                <div style={cards.base}>
                  <div style={{ ...typography.label, marginBottom: '10px' }}>Recommended diversion</div>
                  {result.diversions.map((d, i) => (
                    <div key={d.corridor} style={{
                      padding: '10px', borderRadius: '6px', marginBottom: i < result.diversions.length - 1 ? '8px' : 0,
                      backgroundColor: i === 0 ? '#F0FDF4' : 'var(--color-gray-bg)',
                      border: `1px solid ${i === 0 ? '#059669' : 'var(--color-border)'}30`,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '13px', fontWeight: 600,
                          color: i === 0 ? '#059669' : 'var(--color-text-primary)' }}>
                          {i === 0 ? '✓ ' : `${i + 1}. `}{d.corridor}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
                          {Math.round(d.distance_from_incident_m)}m away
                        </span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                        {d.reason}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Resolution time */}
              {result.resolution_estimate?.predicted_minutes && (
                <div style={cards.base}>
                  <div style={{ ...typography.label, marginBottom: '4px' }}>Predicted clearance</div>
                  <div style={{ ...typography.value, fontSize: '20px' }}>
                    ~{Math.round(result.resolution_estimate.predicted_minutes)} min
                  </div>
                  {result.resolution_estimate.confidence_band && (
                    <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
                      Range: {Math.round(result.resolution_estimate.confidence_band[0])}–
                      {Math.round(result.resolution_estimate.confidence_band[1])} min
                    </div>
                  )}
                </div>
              )}

              {/* Summary */}
              <div style={{
                padding: '12px 14px', borderRadius: '6px', fontSize: '13px', lineHeight: '1.6',
                backgroundColor: 'var(--color-gray-bg)', border: '1px solid var(--color-border)',
                color: 'var(--color-text-secondary)',
              }}>
                {result.summary}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Mode toggle */}
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: '10px' }}>Event type</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              {['unplanned', 'planned'].map(m => (
                <button
                  key={m}
                  onClick={() => { setMode(m); handleReset(); }}
                  style={{
                    ...buttons[mode === m ? 'primary' : 'secondary'],
                    padding: '8px', fontSize: '13px', textAlign: 'center',
                  }}
                >
                  {m === 'unplanned' ? '⚡ Unplanned' : '📅 Planned'}
                </button>
              ))}
            </div>

            {mode === 'planned' && (
              <div style={{ marginTop: '10px' }}>
                <div style={{ ...typography.label, marginBottom: '6px' }}>Event category</div>
                <select
                  value={eventType}
                  onChange={e => setEventType(e.target.value)}
                  style={{
                    width: '100%', padding: '7px 10px', borderRadius: '6px', fontSize: '13px',
                    border: '1px solid var(--color-border)', backgroundColor: 'var(--color-card-bg)',
                    color: 'var(--color-text-primary)', cursor: 'pointer',
                  }}
                >
                  {EVENT_TYPES.map(et => (
                    <option key={et.value} value={et.value}>{et.label}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Map click controls */}
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: '10px' }}>
              {mode === 'unplanned' ? 'Incident location' : 'Event route'}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button
                onClick={() => setClickStep(1)}
                style={{
                  ...buttons[!startPoint ? 'primary' : 'secondary'],
                  padding: '8px 12px', fontSize: '12px', textAlign: 'left',
                  display: 'flex', alignItems: 'center', gap: '8px',
                }}
              >
                <span>📍</span>
                <span>
                  {startPoint
                    ? <span style={{ color: 'inherit' }}>{startPoint.address.substring(0, 38)}…</span>
                    : mode === 'unplanned' ? 'Click map to pin incident' : 'Click map to pin start point'}
                </span>
              </button>

              {mode === 'planned' && (
                <button
                  onClick={() => startPoint && setClickStep(2)}
                  disabled={!startPoint}
                  style={{
                    ...buttons[endPoint ? 'secondary' : 'secondary'],
                    padding: '8px 12px', fontSize: '12px', textAlign: 'left',
                    display: 'flex', alignItems: 'center', gap: '8px',
                    opacity: startPoint ? 1 : 0.45,
                  }}
                >
                  <span>🏁</span>
                  <span>
                    {endPoint
                      ? endPoint.address.substring(0, 38) + '…'
                      : 'Click map to pin end point (optional)'}
                  </span>
                </button>
              )}
            </div>
          </div>

          {/* Description */}
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: '6px' }}>
              {mode === 'unplanned' ? 'Field report' : 'Event description'}
            </div>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder={
                mode === 'unplanned'
                  ? 'ವಾಹನ ಕೆಟ್ಟು ನಿಂತಿದೆ — or type in English…'
                  : 'IPL match at Chinnaswamy, heavy footfall from 5pm…'
              }
              rows={3}
              style={{
                width: '100%', boxSizing: 'border-box',
                padding: '8px 10px', borderRadius: '6px', fontSize: '13px', lineHeight: '1.55',
                border: '1px solid var(--color-border)', backgroundColor: 'var(--color-card-bg)',
                color: 'var(--color-text-primary)', resize: 'vertical',
                fontFamily: "'Inter', 'Noto Sans Kannada', sans-serif",
              }}
            />
            <div style={{ marginTop: '4px', fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
              Kannada, English, or code-mixed — all supported
            </div>
          </div>

          {mode === 'unplanned' && (
            <div style={cards.base}>
              <div style={{ ...typography.label, marginBottom: '10px' }}>
                Rally / event direction
              </div>
              <CompassPicker value={rallyBearing} onChange={setRallyBearing} />
              <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
                Rally moving: {['North','NE','East','SE','South','SW','West','NW'][Math.round(rallyBearing/45)%8]}
              </div>
            </div>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={!startPoint || loading}
            style={{
              ...buttons.primary,
              padding: '10px', fontSize: '14px', fontWeight: 600,
              opacity: !startPoint || loading ? 0.5 : 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}
          >
            {loading ? (
              <>
                <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>
                Analysing…
              </>
            ) : (
              '⚡ Analyse & show diversion'
            )}
          </button>

          {/* Error */}
          {error && (
            <div style={{
              padding: '10px 14px', borderRadius: '6px', fontSize: '13px',
              backgroundColor: '#FEF2F2', border: '1px solid #DC262630', color: '#DC2626',
            }}>
              {error}
            </div>
          )}



        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
import { useEffect, useRef, useState } from 'react';
import { HOTSPOT_JUNCTIONS, CAUSE_TOTALS, TOP_JUNCTIONS } from '../mockData';
import { colors, typography, cards, buttons } from '../styles/globals';

// Helper to generate fake hourly distribution
const getHourlyData = (count) => {
  const dist = [];
  for (let i = 0; i < 24; i++) {
    // Fake bi-modal distribution (morning peak ~8, evening peak ~18)
    const morning = Math.max(0, Math.sin((i - 5) * Math.PI / 6));
    const evening = Math.max(0, Math.sin((i - 15) * Math.PI / 6));
    const noise = Math.random() * 0.2;
    const factor = (morning + evening + noise) / 2.2; 
    dist.push(Math.round(count * factor));
  }
  return dist;
};

// Add hourly data to junctions
const junctionsWithHourly = HOTSPOT_JUNCTIONS.map(j => ({
  ...j,
  hourly: getHourlyData(j.count)
}));

// Helper to create a circle polygon for fill-extrusion
const createCircleGeometry = (lng, lat, radius) => {
  const points = 32;
  const coords = [];
  for (let i = 0; i < points; i++) {
    const angle = (i * 360 / points) * (Math.PI / 180);
    // Roughly adjust for aspect ratio at this latitude
    coords.push([
      lng + (radius * Math.cos(angle)),
      lat + (radius * 0.9 * Math.sin(angle))
    ]);
  }
  coords.push(coords[0]); // close polygon
  return coords;
};

export default function HotspotMap({ searchQuery, onPredictClick }) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const [hoveredRow, setHoveredRow] = useState(null);
  
  // New State
  const [is3D, setIs3D] = useState(true);
  const [selectedJunction, setSelectedJunction] = useState(null);
  const [currentHour, setCurrentHour] = useState(12);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Playback timer ref
  const timerRef = useRef(null);

  // Compute stats
  const totalJunctions = HOTSPOT_JUNCTIONS.length;
  const peakJunc = [...HOTSPOT_JUNCTIONS].sort((a, b) => b.count - a.count)[0];
  const peakJuncText = peakJunc ? `${peakJunc.name.replace(' Junction', '')} (${peakJunc.count})` : 'N/A';
  const causeCounts = {};
  HOTSPOT_JUNCTIONS.forEach(j => {
    causeCounts[j.dominant_cause] = (causeCounts[j.dominant_cause] || 0) + j.count;
  });
  const mostCommonCause = Object.entries(causeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'others';
  const totalEvents = HOTSPOT_JUNCTIONS.reduce((sum, j) => sum + j.count, 0);
  const avgEvents = Math.round(totalEvents / totalJunctions);

  // Initialize MapLibre
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
            attribution: '&copy; OpenStreetMap Contributors',
          }
        },
        layers: [
          {
            id: 'osm',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [77.59, 12.97],
      zoom: 11,
      pitch: 35,
      bearing: 0
    });

    map.on('load', () => {
      // Create GeoJSON source
      const features = junctionsWithHourly.map((j, i) => ({
        type: 'Feature',
        id: i,
        properties: {
          id: i,
          name: j.name,
          count: j.count,
          dominant_cause: j.dominant_cause,
          color: colors.causes[j.dominant_cause] || colors.causes.others,
          height: j.count * 80,
          currentHeight: j.hourly[12] * 80
        },
        geometry: {
          type: 'Polygon',
          coordinates: [createCircleGeometry(j.lng, j.lat, 0.003)] // Approx 300m radius
        }
      }));

      map.addSource('hotspots', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features
        }
      });

      map.addLayer({
        id: 'hotspots-extrusion',
        type: 'fill-extrusion',
        source: 'hotspots',
        paint: {
          'fill-extrusion-color': ['get', 'color'],
          'fill-extrusion-height': ['get', 'currentHeight'],
          'fill-extrusion-base': 0,
          'fill-extrusion-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false], 1,
            ['boolean', ['feature-state', 'selected'], false], 1,
            0.8
          ]
        }
      });

      // Add DOM Markers
      junctionsWithHourly.forEach((j, i) => {
        const el = document.createElement('div');
        el.className = 'map-marker-dom';
        el.id = `marker-${i}`;
        el.style.width = '12px';
        el.style.height = '12px';
        el.style.borderRadius = '50%';
        el.style.backgroundColor = colors.causes[j.dominant_cause] || colors.causes.others;
        el.style.border = '2px solid white';
        el.style.boxShadow = '0 0 4px rgba(0,0,0,0.3)';
        el.style.cursor = 'pointer';
        el.style.transition = 'transform 150ms ease'; // Enforce the requested DOM marker scale

        el.addEventListener('mouseenter', () => {
          el.style.transform = 'scale(1.06)';
          map.setFeatureState({ source: 'hotspots', id: i }, { hover: true });
        });
        
        el.addEventListener('mouseleave', () => {
          el.style.transform = 'scale(1)';
          map.setFeatureState({ source: 'hotspots', id: i }, { hover: false });
        });

        el.addEventListener('click', () => {
          setSelectedJunction(j);
          // Highlight selected
          features.forEach(f => map.setFeatureState({ source: 'hotspots', id: f.id }, { selected: false }));
          map.setFeatureState({ source: 'hotspots', id: i }, { selected: true });
        });

        new window.maplibregl.Marker({ element: el })
          .setLngLat([j.lng, j.lat])
          .addTo(map);
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);



  // Playback Effect
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && isPlaying) {
        setIsPlaying(false);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setCurrentHour(prev => (prev + 1) % 24);
      }, 1000); // 1 sec per hour
    } else {
      clearInterval(timerRef.current);
    }

    return () => {
      clearInterval(timerRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isPlaying]);

  // Update map extrusion heights when hour changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !map.getSource('hotspots')) return;

    const features = junctionsWithHourly.map((j, i) => ({
      type: 'Feature',
      id: i,
      properties: {
        id: i,
        name: j.name,
        count: j.count,
        dominant_cause: j.dominant_cause,
        color: colors.causes[j.dominant_cause] || colors.causes.others,
        height: j.count * 80,
        currentHeight: j.hourly[currentHour] * 80
      },
      geometry: {
        type: 'Polygon',
        coordinates: [createCircleGeometry(j.lng, j.lat, 0.003)]
      }
    }));

    map.getSource('hotspots').setData({
      type: 'FeatureCollection',
      features
    });
  }, [currentHour]);

  // 2D / 3D Toggle
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.easeTo({
      pitch: is3D ? 35 : 0,
      duration: 1000
    });
  }, [is3D]);

  const handleResetView = () => {
    const map = mapRef.current;
    if (!map) return;
    map.flyTo({
      center: [77.59, 12.97],
      zoom: 11,
      pitch: is3D ? 35 : 0,
      bearing: 0
    });
  };

  // Search Filter Effect
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !map.getLayer('hotspots-extrusion')) return;

    const q = searchQuery.toLowerCase().trim();

    if (!q) {
      map.setPaintProperty('hotspots-extrusion', 'fill-extrusion-opacity', [
        'case',
        ['boolean', ['feature-state', 'hover'], false], 1,
        ['boolean', ['feature-state', 'selected'], false], 1,
        0.8
      ]);
      junctionsWithHourly.forEach((_, i) => {
        const el = document.getElementById(`marker-${i}`);
        if (el) el.style.opacity = '1';
      });
      return;
    }

    map.setPaintProperty('hotspots-extrusion', 'fill-extrusion-opacity', [
      'case',
      ['!=', ['index-of', q, ['downcase', ['to-string', ['get', 'name']]]], -1], 0.9,
      ['!=', ['index-of', q, ['downcase', ['to-string', ['get', 'dominant_cause']]]], -1], 0.9,
      0.2 // dim others
    ]);

    junctionsWithHourly.forEach((j, i) => {
      const el = document.getElementById(`marker-${i}`);
      if (el) {
        const isMatch = j.name.toLowerCase().includes(q) || j.dominant_cause.toLowerCase().includes(q);
        el.style.opacity = isMatch ? '1' : '0.2';
      }
    });
  }, [searchQuery]);


  const maxCauseCount = Math.max(...Object.values(CAUSE_TOTALS));
  const sortedCauses = Object.entries(CAUSE_TOTALS).sort((a, b) => b[1] - a[1]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ ...typography.header, margin: 0, fontSize: '16px' }}>Hotspot Map</h1>
          <p style={{ ...typography.subtitle, margin: 0, marginTop: '2px' }}>Historical event density by junction · Bengaluru</p>
        </div>
        <div style={{
          fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: colors.textSecondary,
          backgroundColor: 'var(--color-gray-bg)', border: `1px solid ${colors.border}`, borderRadius: '99px', padding: '4px 10px', fontWeight: 600
        }}>
          6,303 events · ASTRAM dataset
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '65fr 35fr', gap: '16px' }}>
        
        {/* Left - Map Area */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          
          <div style={{
            border: `1px solid ${colors.border}`,
            borderRadius: '8px',
            overflow: 'hidden',
            height: '520px',
            position: 'relative',
            backgroundColor: 'var(--color-map-bg)'
          }}>
            {/* Map Container */}
            <div ref={mapContainer} style={{ width: '100%', height: '100%', outline: 'none' }} />

            {/* Map Controls */}
            <div style={{ position: 'absolute', top: '12px', left: '12px', zIndex: 10, display: 'flex', gap: '8px' }}>
              <button onClick={() => setIs3D(!is3D)} style={{ ...buttons.secondary, padding: '4px 8px', fontSize: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                {is3D ? '2D View' : '3D View'}
              </button>
              <button onClick={handleResetView} style={{ ...buttons.secondary, padding: '4px 8px', fontSize: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                Reset View
              </button>
            </div>

            {/* Drawer Panel */}
            <div style={{
              position: 'absolute', top: 0, bottom: 0, right: 0, width: '400px',
              backgroundColor: 'var(--color-card-bg)', borderLeft: `1px solid ${colors.border}`,
              transform: selectedJunction ? 'translateX(0)' : 'translateX(100%)',
              transition: 'transform 300ms ease', zIndex: 20, padding: '24px', boxSizing: 'border-box',
              display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto'
            }}>
              {selectedJunction && (
                <>
                  <button onClick={() => setSelectedJunction(null)} style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px', color: colors.textSecondary }}>✕</button>
                  <h2 style={{ ...typography.header, fontSize: '18px', margin: 0 }}>{selectedJunction.name}</h2>
                  
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, padding: '4px 10px', borderRadius: '99px', backgroundColor: '#EFF6FF', color: colors.accent, border: `1px solid ${colors.accent}30` }}>
                      {selectedJunction.count} Events Total
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', padding: '4px 10px', borderRadius: '99px', backgroundColor: `${colors.causes[selectedJunction.dominant_cause]}15`, color: colors.causes[selectedJunction.dominant_cause], border: `1px solid ${colors.causes[selectedJunction.dominant_cause]}30` }}>
                      {selectedJunction.dominant_cause.replace('_', ' ')}
                    </span>
                  </div>

                  <div>
                    <div style={{ ...typography.label, marginBottom: '4px' }}>Avg Resolution Time</div>
                    <div style={{ ...typography.value, fontSize: '16px' }}>54 min avg</div>
                  </div>

                  <div>
                    <div style={{ ...typography.label, marginBottom: '4px' }}>Jurisdiction</div>
                    <div style={{ ...typography.body }}>{selectedJunction.name.split(' ')[0]} Traffic PS</div>
                  </div>

                  {/* Mini Bar Chart */}
                  <div>
                    <div style={{ ...typography.label, marginBottom: '12px' }}>Top Event Causes</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {['vehicle_breakdown', 'accident', 'water_logging'].map((cause, idx) => {
                        const val = Math.round(selectedJunction.count * (1 - idx * 0.3)); // mock data split
                        const pct = (val / selectedJunction.count) * 100;
                        return (
                          <div key={cause} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '12px', width: '120px', color: colors.textSecondary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{cause.replace('_', ' ')}</span>
                            <div style={{ flexGrow: 1, height: '6px', backgroundColor: 'var(--color-gray-bg)', borderRadius: '99px' }}>
                              <div style={{ height: '100%', width: `${pct}%`, backgroundColor: colors.causes[cause] || colors.textSecondary, borderRadius: '99px' }} />
                            </div>
                            <span style={{ fontSize: '12px', fontWeight: 500, width: '24px', textAlign: 'right' }}>{val}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
                    <button 
                      style={{ ...buttons.primary, width: '100%' }}
                      onClick={() => onPredictClick({ corridor: 'CBD 1', policeStation: selectedJunction.name.split(' ')[0] })}
                    >
                      Predict impact for this junction →
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Timeline Playback Scrubber */}
          <div style={{ ...cards.base, padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button onClick={() => setIsPlaying(!isPlaying)} style={{ ...buttons.secondary, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </button>
            <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ ...typography.label, width: '80px' }}>Hour: {currentHour.toString().padStart(2, '0')}:00</span>
              <input 
                type="range" 
                min="0" max="23" step="1" 
                value={currentHour} 
                onChange={(e) => { setCurrentHour(parseInt(e.target.value)); setIsPlaying(false); }}
                style={{ flexGrow: 1, cursor: 'pointer' }}
              />
            </div>
          </div>

        </div>

        {/* Right - Stacked Stat Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Card 1: 2x2 Grid */}
          <div style={cards.base}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <div style={typography.label}>Total junctions</div>
                <div style={{ ...typography.value, fontSize: '18px', marginTop: '4px' }}>{totalJunctions}</div>
              </div>
              <div>
                <div style={typography.label}>Peak junction</div>
                <div style={{ ...typography.value, fontSize: '14px', marginTop: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={peakJuncText}>
                  {peakJuncText}
                </div>
              </div>
              <div style={{ borderTop: `1px solid ${colors.border}`, paddingTop: '12px' }}>
                <div style={typography.label}>Most common cause</div>
                <div style={{ ...typography.value, fontSize: '13px', marginTop: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={mostCommonCause}>
                  {mostCommonCause}
                </div>
              </div>
              <div style={{ borderTop: `1px solid ${colors.border}`, paddingTop: '12px' }}>
                <div style={typography.label}>Avg events/junction</div>
                <div style={{ ...typography.value, fontSize: '18px', marginTop: '4px' }}>{avgEvents}</div>
              </div>
            </div>
          </div>

          {/* Card 2: Cause Legend */}
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: '12px' }}>Event Causes</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {sortedCauses.map(([cause, count]) => {
                const color = colors.causes[cause] || colors.causes.others;
                const percentage = (count / maxCauseCount) * 100;
                return (
                  <div key={cause} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', width: '130px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color, flexShrink: 0 }} />
                      <span style={{ ...typography.body, fontSize: '12px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: colors.textSecondary }}>
                        {cause}
                      </span>
                    </div>
                    <div style={{ flexGrow: 1, height: '4px', backgroundColor: 'var(--color-gray-bg)', borderRadius: '99px', position: 'relative' }}>
                      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${percentage}%`, backgroundColor: color, borderRadius: '99px' }} />
                    </div>
                    <div style={{ ...typography.value, fontSize: '12px', color: colors.textSecondary, width: '30px', textAlign: 'right', flexShrink: 0 }}>
                      {count}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Card 3: Top 5 Junctions */}
          <div style={{ ...cards.base, padding: '16px 20px' }}>
            <div style={{ ...typography.label, marginBottom: '8px' }}>Top Junctions by Volume</div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                {TOP_JUNCTIONS.map((junc, index) => (
                  <tr
                    key={junc.name}
                    style={{
                      borderBottom: index < TOP_JUNCTIONS.length - 1 ? `1px solid ${colors.border}` : 'none',
                      backgroundColor: hoveredRow === index ? 'var(--color-hover-bg)' : 'transparent',
                      transition: 'background-color 150ms ease',
                      cursor: 'default'
                    }}
                    onMouseEnter={() => setHoveredRow(index)}
                    onMouseLeave={() => setHoveredRow(null)}
                  >
                    <td style={{ ...typography.body, fontSize: '12px', color: colors.textTertiary, padding: '8px 4px', width: '24px' }}>
                      {index + 1}
                    </td>
                    <td style={{ ...typography.body, fontSize: '13px', fontWeight: 500, color: colors.textPrimary, padding: '8px 4px' }}>
                      {junc.name}
                    </td>
                    <td style={{ ...typography.value, fontSize: '13px', color: colors.textSecondary, padding: '8px 4px', textAlign: 'right' }}>
                      {junc.count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { colors, typography, cards, buttons } from '../styles/globals';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function PredictEvent({ initialData }) {
  // Form state
  const [eventCause, setEventCause] = useState('public_event');
  const [corridor, setCorridor] = useState('CBD 1');
  const [policeStation, setPoliceStation] = useState('Cubbon Park');
  const [requiresRoadClosure, setRequiresRoadClosure] = useState(false);
  const [description, setDescription] = useState('');

  // Handle pre-fill from Hotspot Map Drawer
  useEffect(() => {
    if (initialData) {
      if (initialData.corridor) setCorridor(initialData.corridor);
      if (initialData.policeStation) setPoliceStation(initialData.policeStation);
    }
  }, [initialData]);

  // UI state: 'default' | 'loading' | 'result'
  const [uiState, setUiState] = useState('default');
  const [result, setResult] = useState(null);
  
  // Scenarios State
  const [savedScenarios, setSavedScenarios] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setUiState('loading');
    setResult(null);

    const formData = {
      event_cause: eventCause,
      corridor,
      police_station: policeStation,
      requires_road_closure: requiresRoadClosure,
      description
    };

    try {
      const res = await fetch(`${API_BASE}/events/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: formData.description || `Event of type ${formData.event_cause}`,
          corridor: formData.corridor,
          police_station: formData.police_station,
          requires_road_closure: formData.requires_road_closure,
          latitude: 12.9716, // Default for prediction UI
          longitude: 77.5946,
          event_type: 'planned'
        })
      });
      const data = await res.json();
      
      const resEst = data.resolution_estimate || {};
      const bestMatch = (data.text_similar_reports && data.text_similar_reports.length > 0) 
        ? data.text_similar_reports[0] 
        : (data.precedent && data.precedent.matches && data.precedent.matches.length > 0)
          ? data.precedent.matches[0]
          : null;

      setResult({
        matched_event_id: bestMatch ? `EVT-${bestMatch.id}` : 'N/A',
        matched_description: bestMatch ? bestMatch.description : 'No similar historical event found',
        predicted_minutes: resEst.predicted_minutes || 0,
        confidence_band: resEst.confidence_band || 'N/A',
        manpower_tier: resEst.manpower_tier || 'N/A',
        explanation: resEst.explanation || 'No explanation available',
        _formData: formData
      });
      setUiState('result');
    } catch (err) {
      console.error(err);
      setUiState('default');
    }
  };

  const handleSaveScenario = () => {
    if (result && savedScenarios.length < 3) {
      setSavedScenarios([...savedScenarios, result]);
    }
  };

  const stations = [
    'Cubbon Park', 'High Grounds', 'Ulsoor', 'Shivajinagar',
    'Commercial Street', 'Koramangala', 'HSR Layout', 'Indiranagar',
    'Madivala', 'Silk Board', 'Whitefield', 'Bellandur', 'Hebbal',
    'Jayanagar', 'JP Nagar'
  ];

  const corridors = [
    'Airport New South Road', 'Bannerghata Road', 'Bellary Road 1', 'Bellary Road 2', 
    'CBD 1', 'CBD 2', 'Hennur Main Road', 'Hosur Road', 'IRR(Thanisandra road)', 
    'Magadi Road', 'Mysore Road', 'ORR East 1', 'ORR East 2', 'ORR North 1', 
    'ORR North 2', 'ORR West 1', 'Old Airport Road', 'Old Madras Road', 'Tumkur Road', 
    'Varthur Road', 'West of Chord Road'
  ];

  const causes = [
    'public_event', 'procession', 'vip_movement', 'construction',
    'vehicle_breakdown', 'accident', 'water_logging',
    'tree_fall', 'pot_holes', 'congestion'
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Row */}
      <div>
        <h1 style={{ ...typography.header, margin: 0, fontSize: '16px' }}>Predict Event Impact</h1>
        <p style={{ ...typography.subtitle, margin: 0, marginTop: '2px' }}>Estimate congestion clearance time for a planned event</p>
      </div>

      {/* Main Two-Column Layout (45/55) */}
      <div style={{ display: 'grid', gridTemplateColumns: '45fr 55fr', gap: '16px', alignItems: 'start' }}>
        
        {/* Left Column - Form Card */}
        <div style={cards.base}>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ ...typography.label, borderBottom: `1px solid ${colors.border}`, paddingBottom: '8px' }}>Event Details</div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={typography.label}>Event Cause</label>
              <select value={eventCause} onChange={(e) => setEventCause(e.target.value)} style={{ padding: '8px 12px', borderRadius: '6px', border: `1px solid ${colors.border}`, fontSize: '13px', fontFamily: typography.fontFamily, color: colors.textPrimary, backgroundColor: 'var(--color-bg)', outline: 'none' }}>
                {causes.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={typography.label}>Corridor</label>
              <select value={corridor} onChange={(e) => setCorridor(e.target.value)} style={{ padding: '8px 12px', borderRadius: '6px', border: `1px solid ${colors.border}`, fontSize: '13px', fontFamily: typography.fontFamily, color: colors.textPrimary, backgroundColor: 'var(--color-bg)', outline: 'none' }}>
                {corridors.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={typography.label}>Police Station</label>
              <select value={policeStation} onChange={(e) => setPoliceStation(e.target.value)} style={{ padding: '8px 12px', borderRadius: '6px', border: `1px solid ${colors.border}`, fontSize: '13px', fontFamily: typography.fontFamily, color: colors.textPrimary, backgroundColor: 'var(--color-bg)', outline: 'none' }}>
                {stations.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
              <span style={{ ...typography.body, fontSize: '13px', color: colors.textPrimary }}>Requires road closure</span>
              <div onClick={() => setRequiresRoadClosure(!requiresRoadClosure)} style={{ width: '36px', height: '20px', borderRadius: '99px', backgroundColor: requiresRoadClosure ? colors.accent : '#E5E7EB', display: 'flex', alignItems: 'center', padding: '2px', cursor: 'pointer', transition: 'background-color 150ms ease', position: 'relative' }}>
                <div style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: 'var(--color-card-bg)', position: 'absolute', left: requiresRoadClosure ? '18px' : '2px', transition: 'left 150ms ease' }} />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={typography.label}>Description</label>
              <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Describe the event in English or Kannada... ಕಾರ್ಯಕ್ರಮದ ವಿವರಣೆ ನಮೂದಿಸಿ..." style={{ padding: '8px 12px', borderRadius: '6px', border: `1px solid ${colors.border}`, fontSize: '13px', fontFamily: typography.fontFamily, color: colors.textPrimary, backgroundColor: 'var(--color-bg)', outline: 'none', resize: 'vertical', lineHeight: '1.4' }} />
            </div>

            <button type="submit" disabled={uiState === 'loading'} style={{ ...buttons.primary, opacity: uiState === 'loading' ? 0.6 : 1, cursor: uiState === 'loading' ? 'not-allowed' : 'pointer', marginTop: '8px' }}>
              Predict impact →
            </button>
          </form>
        </div>

        {/* Right Column - Result Panel */}
        <div>
          {uiState === 'default' && (
            <div style={{ backgroundColor: 'var(--color-bg)', border: `1px dashed ${colors.border}`, borderRadius: '8px', height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: colors.textSecondary, fontFamily: typography.fontFamily, fontSize: '13px' }}>
              Run a prediction to see results
            </div>
          )}

          {uiState === 'loading' && (
            <div style={{ ...cards.base, height: '280px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '12px' }}>
              <div style={{ height: '14px', width: '30%', borderRadius: '4px', animation: 'sweep 1.2s linear infinite', backgroundImage: 'linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)', backgroundSize: '200% 100%' }} />
              <div style={{ height: '18px', width: '70%', borderRadius: '4px', animation: 'sweep 1.2s linear infinite', backgroundImage: 'linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)', backgroundSize: '200% 100%' }} />
              <div style={{ height: '1px', backgroundColor: colors.border, margin: '8px 0' }} />
              <div style={{ height: '40px', width: '100%', borderRadius: '4px', animation: 'sweep 1.2s linear infinite', backgroundImage: 'linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)', backgroundSize: '200% 100%' }} />
              <div style={{ height: '60px', width: '100%', borderRadius: '4px', animation: 'sweep 1.2s linear infinite', backgroundImage: 'linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)', backgroundSize: '200% 100%' }} />
            </div>
          )}

          {uiState === 'result' && result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={cards.base}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '11px', color: colors.accent, backgroundColor: '#EFF6FF', padding: '2px 6px', borderRadius: '4px', fontWeight: 600, border: `1px solid ${colors.accent}20` }}>
                      {result.matched_event_id}
                    </span>
                    <span style={{ ...typography.subtitle, fontSize: '11px' }}>MATCHED ARCHIVE</span>
                  </div>

                  <h3 style={{ ...typography.value, fontSize: '14px', margin: 0, fontWeight: 600 }}>
                    {result.matched_description}
                  </h3>

                  <div style={{ height: '1px', backgroundColor: colors.border }} />

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                    <div>
                      <div style={typography.label}>Clearance Time</div>
                      <div style={{ ...typography.value, fontSize: '15px', color: colors.textPrimary, marginTop: '4px' }}>
                        {result.predicted_minutes} min
                      </div>
                    </div>
                    <div>
                      <div style={typography.label}>Confidence</div>
                      <div style={{ ...typography.value, fontSize: '15px', color: colors.success, marginTop: '4px' }}>
                        {result.confidence_band}
                      </div>
                    </div>
                    <div>
                      <div style={typography.label}>Manpower</div>
                      <div style={{ ...typography.value, fontSize: '15px', color: colors.warning, marginTop: '4px' }}>
                        {result.manpower_tier}
                      </div>
                    </div>
                  </div>

                  <div style={{ height: '1px', backgroundColor: colors.border }} />

                  <div style={{ borderLeft: `3px solid ${colors.accent}`, backgroundColor: 'var(--color-bg)', padding: '12px', borderRadius: '0 6px 6px 0' }}>
                    <p style={{ ...typography.body, fontSize: '13px', margin: 0 }}>
                      {result.explanation}
                    </p>
                  </div>

                  <div style={{ fontFamily: 'monospace', fontSize: '11px', color: colors.textTertiary, textAlign: 'center', marginTop: '4px', borderTop: `1px solid ${colors.border}`, paddingTop: '10px' }}>
                    Live prediction from DRISHTI backend
                  </div>
                </div>
              </div>

              {/* Save Scenario Button */}
              {savedScenarios.length < 3 && (
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button onClick={handleSaveScenario} style={{ ...buttons.secondary, fontSize: '12px', padding: '6px 12px' }}>
                    Save scenario
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

      </div>

      {/* Scenario Comparison Section */}
      {savedScenarios.length > 0 && (
        <div style={{ marginTop: '12px', paddingTop: '16px', borderTop: `1px dashed ${colors.border}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h2 style={{ ...typography.label, fontSize: '12px', margin: 0 }}>Scenario Comparison</h2>
            <button onClick={() => setSavedScenarios([])} style={{ background: 'none', border: 'none', color: colors.accent, fontSize: '12px', cursor: 'pointer', fontFamily: typography.fontFamily }}>
              Clear all
            </button>
          </div>
          
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {savedScenarios.map((scenario, idx) => {
              const causeColor = colors.causes[scenario._formData.event_cause] || colors.causes.others;
              return (
                <div key={idx} style={{ ...cards.base, width: '220px', padding: '16px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <span style={{ alignSelf: 'flex-start', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', padding: '2px 8px', borderRadius: '99px', backgroundColor: `${causeColor}15`, color: causeColor, border: `1px solid ${causeColor}30` }}>
                      {scenario._formData.event_cause.replace('_', ' ')}
                    </span>
                    <div style={{ ...typography.body, fontSize: '12px', color: colors.textSecondary }}>
                      {scenario._formData.corridor} · {scenario._formData.police_station}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                      <span style={{ ...typography.value, fontSize: '20px' }}>{scenario.predicted_minutes}</span>
                      <span style={{ ...typography.subtitle, fontSize: '11px' }}>min</span>
                    </div>
                    <div style={{ height: '1px', backgroundColor: colors.border }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontFamily: typography.fontFamily }}>
                      <span style={{ color: colors.textSecondary }}>Tier:</span>
                      <span style={{ color: colors.warning, fontWeight: 500 }}>{scenario.manpower_tier}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontFamily: typography.fontFamily }}>
                      <span style={{ color: colors.textSecondary }}>Conf:</span>
                      <span style={{ color: colors.success, fontWeight: 500 }}>{scenario.confidence_band}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}

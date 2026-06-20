import { useState, useEffect } from 'react';
import { colors, typography, cards, buttons } from '../styles/globals';

export default function PredictEvent({ initialData, onPredictionSuccess }) {
  // Form state
  const [eventCause, setEventCause] = useState('public_event');
  const [corridor, setCorridor] = useState('CBD 1');
  const [policeStation, setPoliceStation] = useState('Cubbon Park');
  const [requiresRoadClosure, setRequiresRoadClosure] = useState(false);
  const [description, setDescription] = useState('');

  // Handle pre-fill from Hotspot Map Drawer
  useEffect(() => {
    if (initialData) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (initialData.corridor) setCorridor(initialData.corridor);
      // eslint-disable-next-line react-hooks/set-state-in-effect
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
      const response = await fetch('/api/events/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: description || 'No description provided.',
          corridor,
          police_station: policeStation,
          latitude: 12.9716, // Dummy value
          longitude: 77.5946, // Dummy value
          requires_road_closure: requiresRoadClosure,
          event_type: 'planned'
        })
      });

      if (!response.ok) throw new Error('API failed');
      const data = await response.json();

      if (onPredictionSuccess) onPredictionSuccess(data);

      const topMatch = data.precedent?.matches?.[0];
      const confBand = data.resolution_estimate?.confidence_band;
      const formattedConf = Array.isArray(confBand) ? `${confBand[0]} - ${confBand[1]}` : (confBand || 'Low');
      const causeText = formData.event_cause.replace('_', ' ');
      const fallbackExplanation = `Historical data for ${causeText} incidents at ${formData.police_station} indicates a typical clearance time of ${data.resolution_estimate?.predicted_minutes || 0} minutes.`;

      setResult({ 
        matched_event_id: topMatch?.source_id || data.logged_event_id || 'N/A',
        matched_description: topMatch?.description || 'No matching precedent found.',
        predicted_minutes: data.resolution_estimate?.predicted_minutes || 0,
        confidence_band: formattedConf,
        manpower_tier: data.resolution_estimate?.manpower_tier || 'Standard',
        explanation: data.resolution_estimate?.explanation || fallbackExplanation,
        _formData: formData,
        precedent_confidence: data.precedent?.confidence?.confidence_tier || 'unknown',
        low_precedent: data.precedent?.confidence?.low_precedent || false
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
    'CBD 1', 'CBD 2', 'ORR East 1', 'ORR East 2', 'ORR West 1',
    'ORR West 2', 'Mysore Road', 'Old Madras Road', 'Hosur Road',
    'Tumkur Road', 'Bellary Road', 'Bannerghatta Road', 'Sarjapura Road',
    'Non-corridor'
  ];

  const causes = [
    'public_event', 'procession', 'vip_movement', 'construction',
    'protest', 'vehicle_breakdown', 'accident', 'water_logging',
    'tree_fall', 'road_conditions', 'congestion'
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
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', color: colors.textTertiary, letterSpacing: '0.05em' }}>
                        Similar Past Event
                      </span>
                      <span style={{ fontSize: '11px', color: colors.accent, fontWeight: 600, backgroundColor: '#EFF6FF', padding: '2px 8px', borderRadius: '4px' }}>
                        {result.matched_event_id}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      {result.low_precedent && (
                        <span style={{ fontSize: '11px', color: '#DC2626', backgroundColor: '#FEE2E2', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                          LOW PRECEDENT
                        </span>
                      )}
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', color: colors.textTertiary, letterSpacing: '0.05em' }}>
                        Confidence: {result.precedent_confidence}
                      </span>
                    </div>
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

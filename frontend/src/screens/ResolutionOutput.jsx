import { useState, useEffect, useRef } from 'react';
import { colors, typography, cards } from '../styles/globals';

export default function ResolutionOutput({ predictionData }) {
  const [showRawOutput, setShowRawOutput] = useState(false);
  
  const data = predictionData ? {
    predicted_minutes: predictionData.resolution_estimate?.predicted_minutes || 0,
    confidence_band: predictionData.resolution_estimate?.confidence_band || 'N/A',
    manpower_tier: predictionData.resolution_estimate?.manpower_tier || 'N/A',
    explanation: predictionData.resolution_estimate?.explanation || 'N/A',
    similar_events: (predictionData.precedent?.matches || []).map(m => ({
      name: m.description,
      corridor: m.corridor || 'Unknown',
      duration: m.duration_minutes || '?'
    })),
    raw: predictionData
  } : null;

    const [activeStage, setActiveStage] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const timerRef = useRef(null);
  
    useEffect(() => {
      if (isPlaying) {
        if (activeStage >= 5) {
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setIsPlaying(false);
          return;
        }
      timerRef.current = setInterval(() => {
        setActiveStage(s => {
          if (s >= 4) {
            setIsPlaying(false);
            return 5;
          }
          return s + 1;
        });
      }, 1500);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isPlaying, activeStage]);

  const stages = [
    { label: 'Event reported', pct: 0 },
    { label: 'Officers dispatched', pct: 0.15 },
    { label: 'Diversion active', pct: 0.40 },
    { label: 'Traffic normalising', pct: 0.75 },
    { label: 'Road cleared', pct: 1.0 }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {!data ? (
        <div style={{ ...cards.base, textAlign: 'center', padding: '40px', color: colors.textSecondary }}>
          <p>No prediction data available.</p>
          <p style={{ fontSize: '13px' }}>Please run a prediction in the "Predict Event" tab to view the detailed resolution output here.</p>
        </div>
      ) : (
        <>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h1 style={{ ...typography.header, margin: 0, fontSize: '16px' }}>Resolution Output</h1>
          {data.raw?.precedent?.confidence?.low_precedent && (
            <span style={{ fontSize: '11px', color: '#B45309', backgroundColor: '#FEF3C7', padding: '2px 8px', borderRadius: '4px', fontWeight: 600, border: '1px solid #FDE68A' }}>
              Low Historical Precedent Warning
            </span>
          )}
        </div>
        <p style={{ ...typography.subtitle, margin: 0, marginTop: '2px' }}>Model output for a classified or planned event</p>
      </div>

      {/* 40/60 Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '40fr 60fr', gap: '16px', alignItems: 'start' }}>
        
        {/* Left Column - 3 Stacked Metric Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Card 1: Predicted Clearance */}
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: '4px' }}>Predicted Clearance</div>
            {/* Font size restricted to 20px per max size constraint */}
            <div style={{ fontFamily: typography.fontFamily, fontSize: '20px', fontWeight: '400', color: colors.textPrimary }}>
              {data.predicted_minutes} min
            </div>
            <div style={{ ...typography.subtitle, marginTop: '2px', marginBottom: '12px' }}>
              ≈ 4 hours from event start
            </div>
            {/* Progress bar */}
            <div style={{ height: '4px', backgroundColor: 'var(--color-border)', borderRadius: '99px', width: '100%', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: '50%', backgroundColor: colors.warning, borderRadius: '99px' }} />
            </div>
          </div>

          {/* Card 2: Confidence Band */}
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: '4px' }}>Confidence Band</div>
            <div style={{ ...typography.value, fontSize: '18px', color: colors.success, fontWeight: '600' }}>
              {data.confidence_band}
            </div>
            <div style={{ ...typography.subtitle, marginTop: '4px' }}>
              Based on 47 similar historical events
            </div>
          </div>

          {/* Card 3: Manpower Tier */}
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: '4px' }}>Manpower Tier</div>
            <div style={{ ...typography.value, fontSize: '18px', color: colors.warning, fontWeight: '600' }}>
              {data.manpower_tier}
            </div>
            <div style={{ ...typography.subtitle, marginTop: '4px' }}>
              Deploy 8–12 officers + 1 tow unit
            </div>
          </div>

        </div>

        {/* Right Column - Detail Card */}
        <div style={{ ...cards.base, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Explanation Section */}
          <div>
            <div style={{ ...typography.label, marginBottom: '8px' }}>Explanation</div>
            <div style={{
              borderLeft: `3px solid ${colors.accent}`,
              backgroundColor: 'var(--color-bg)',
              padding: '12px',
              borderRadius: '0 6px 6px 0'
            }}>
              <p style={{ ...typography.body, margin: 0 }}>
                {data.explanation}
              </p>
            </div>
          </div>

          {/* Similar Historical Events Section */}
          <div>
            <div style={{ ...typography.label, marginBottom: '8px' }}>Similar Historical Events</div>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '8px' }}>
              <tbody>
                {data.similar_events.map((evt, idx) => (
                  <tr key={idx} style={{ borderBottom: `1px solid ${colors.border}`, transition: 'background-color 150ms ease' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F9FAFB'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                    <td style={{ ...typography.body, padding: '8px 4px', fontWeight: '500' }}>{evt.name}</td>
                    <td style={{ ...typography.body, padding: '8px 4px', color: colors.textSecondary }}>{evt.corridor}</td>
                    <td style={{ ...typography.body, padding: '8px 4px', textAlign: 'right' }}>{evt.duration} min</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ fontSize: '11px', color: colors.textTertiary, fontFamily: typography.fontFamily }}>
              Retrieved from ASTRAM memory store · 2,524 validated records
            </div>
          </div>

          {/* Severity Section */}
          <div>
            <div style={{ ...typography.label, marginBottom: '8px' }}>Severity</div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{
                fontSize: '11px', fontWeight: '600', padding: '4px 10px', borderRadius: '99px',
                backgroundColor: '#FEF2F2', color: '#DC2626', border: '1px solid #FECACA'
              }}>
                High priority
              </span>
              <span style={{
                fontSize: '11px', fontWeight: '600', padding: '4px 10px', borderRadius: '99px',
                backgroundColor: '#F0FDF4', color: '#059669', border: '1px solid #DCFCE7'
              }}>
                Road closure: No
              </span>
              <span style={{
                fontSize: '11px', fontWeight: '600', padding: '4px 10px', borderRadius: '99px',
                backgroundColor: '#FFFBEB', color: '#D97706', border: '1px solid #FEF3C7'
              }}>
                Unplanned event
              </span>
            </div>
          </div>

          {/* Collapsible Raw Model Output */}
          <div style={{ marginTop: '8px', borderTop: `1px solid ${colors.border}`, paddingTop: '16px' }}>
            <div 
              style={{ ...typography.body, fontSize: '13px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
              onClick={() => setShowRawOutput(!showRawOutput)}
            >
              Raw model output {showRawOutput ? '↑' : '↓'}
            </div>
            {showRawOutput && (
              <div style={{ 
                marginTop: '12px', 
                backgroundColor: 'var(--color-bg)', 
                border: `1px solid ${colors.border}`, 
                borderRadius: '6px', 
                padding: '16px', 
                fontSize: '13px', 
                color: colors.textSecondary 
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '12px', lineHeight: '1.5' }}>
                  <strong style={{ color: colors.textPrimary }}>Model Engine:</strong> 
                  <span>{data.raw?.method?.toUpperCase() || 'N/A'}</span>
                  
                  <strong style={{ color: colors.textPrimary }}>Classification:</strong> 
                  <div>
                    Cause: {data.raw?.classification?.event_cause?.replace('_', ' ')} ({(data.raw?.classification?.cause_confidence * 100)?.toFixed(1)}%)<br/>
                    Severity: {data.raw?.classification?.severity} ({(data.raw?.classification?.severity_confidence * 100)?.toFixed(1)}%)
                  </div>

                  <strong style={{ color: colors.textPrimary }}>Civic Routing:</strong> 
                  <span>
                    {(data.raw?.classification?.routing?.routing_agency || 'N/A').toUpperCase()}
                    {data.raw?.classification?.routing?.is_ambiguous ? ' (Ambiguous)' : ''}
                  </span>

                  <strong style={{ color: colors.textPrimary }}>Historical Precedent:</strong> 
                  <div>
                    Total matches found: {data.raw?.precedent?.total_matches || 0}<br/>
                    Confidence Tier: {data.raw?.precedent?.confidence?.confidence_tier?.toUpperCase() || 'N/A'} (Count: {data.raw?.precedent?.confidence?.precedent_count || 0})
                  </div>
                  
                  <strong style={{ color: colors.textPrimary }}>Estimate Bounds:</strong>
                  <span>{data.raw?.resolution_estimate?.confidence_band} mins</span>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Resolution Simulation Timeline */}
      <div style={{ ...cards.base, marginTop: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ ...typography.label, fontSize: '13px', margin: 0 }}>Resolution Simulation Timeline</h2>
          <button 
            onClick={() => {
              if (activeStage >= 5) setActiveStage(0);
              setIsPlaying(!isPlaying);
            }} 
            style={{ 
              backgroundColor: 'var(--color-card-bg)', color: colors.textPrimary, border: `1px solid ${colors.border}`, 
              borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: 500, 
              cursor: 'pointer', transition: 'all 150ms ease, background-color 150ms ease, color 150ms ease',
              display: 'flex', alignItems: 'center', gap: '6px'
            }}
          >
            {isPlaying ? '⏸ Pause' : (activeStage >= 5 ? '↻ Replay' : '▶ Simulate')}
          </button>
        </div>

        <div style={{ display: 'flex', position: 'relative', justifyContent: 'space-between' }}>
          {/* Background Track Line */}
          <div style={{ position: 'absolute', top: '10px', left: '20px', right: '20px', height: '2px', backgroundColor: 'var(--color-border)', zIndex: 0 }} />
          
          {/* Active Track Line */}
          <div style={{ position: 'absolute', top: '10px', left: '20px', width: `${Math.min(100, Math.max(0, activeStage / (stages.length - 1)) * 100)}%`, height: '2px', backgroundColor: colors.accent, zIndex: 1, transition: 'width 300ms ease' }} />

          {stages.map((stage, idx) => {
            const isCompleted = activeStage > idx;
            const isCurrent = activeStage === idx;
            
            let circleBg = 'var(--color-card-bg)';
            let circleBorder = `2px solid var(--color-border)`;
            let icon = null;

            if (isCompleted) {
              circleBg = colors.accent;
              circleBorder = `2px solid ${colors.accent}`;
              icon = <span style={{ color: '#FFFFFF', fontSize: '10px', fontWeight: 'bold' }}>✓</span>;
            } else if (isCurrent) {
              circleBg = colors.accent;
              circleBorder = `2px solid ${colors.accent}`;
            }

            return (
              <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2, width: '120px' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: circleBg, border: circleBorder, display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 300ms ease', boxSizing: 'border-box' }}>
                  {icon}
                </div>
                <div style={{ ...typography.body, fontSize: '12px', marginTop: '8px', fontWeight: (isCurrent || isCompleted) ? 600 : 400, color: (isCurrent || isCompleted) ? colors.textPrimary : colors.textSecondary, textAlign: 'center' }}>
                  {stage.label}
                </div>
                <div style={{ ...typography.subtitle, fontSize: '11px', marginTop: '4px' }}>
                  +{Math.round(data.predicted_minutes * stage.pct)} min
                </div>
              </div>
            );
          })}
        </div>
      </div>
      </>
      )}
    </div>
  );
}

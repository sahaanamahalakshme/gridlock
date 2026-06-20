import { useState } from 'react';
import { colors, typography, cards, buttons } from '../styles/globals';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function Classifier() {
  const [text, setText] = useState('');
  const [policeStation, setPoliceStation] = useState('');
  const [uiState, setUiState] = useState('default'); // 'default' | 'loading' | 'result'
  const [result, setResult] = useState(null);

  const characterCount = text.length;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setUiState('loading');
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: text, police_station: policeStation })
      });
      const data = await res.json();
      setResult(data);
      setUiState('result');
    } catch (err) {
      console.error(err);
      setUiState('default');
    }
  };

  const loadExample = (exampleText) => {
    setText(exampleText);
    // Reset result state if we choose another template
    setUiState('default');
    setResult(null);
  };

  // Sample data templates
  const examples = {
    english: "Accident reported near Hebbal flyover between a car and a two-wheeler, heavy congestion building up.",
    kannada: "ಮೆಜೆಸ್ಟಿಕ್ ಬಳಿ ಬಿಎಂಟಿಸಿ ಬಸ್ ಕೆಟ್ಟು ನಿಂತಿದ್ದರಿಂದ ಟ್ರಾಫಿಕ್ ಜಾಮ್ ಆಗಿದೆ.",
    codeMixed: "Silk Board junction hatra vehicle breakdown agide, please clear it immediately."
  };

  const stations = [
    '', 'Cubbon Park', 'High Grounds', 'Ulsoor', 'Shivajinagar',
    'Commercial Street', 'Koramangala', 'HSR Layout', 'Indiranagar',
    'Madivala', 'Silk Board', 'Whitefield', 'Bellandur', 'Hebbal',
    'Jayanagar', 'JP Nagar'
  ];

  const causeColor = result ? (colors.causes[result.event_cause] || colors.causes.others) : colors.textSecondary;

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header Row */}
      <div>
        <h1 style={{ ...typography.header, margin: 0, fontSize: '16px' }}>Field Report Classifier</h1>
        <p style={{ ...typography.subtitle, margin: 0, marginTop: '2px' }}>Paste a raw report in English or Kannada</p>
      </div>

      {/* Input Card */}
      <div style={cards.base}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={typography.label}>Police Station (Optional)</label>
            <select 
              value={policeStation} 
              onChange={(e) => setPoliceStation(e.target.value)} 
              style={{ padding: '8px 12px', borderRadius: '6px', border: `1px solid ${colors.border}`, fontSize: '13px', fontFamily: typography.fontFamily, color: colors.textPrimary, backgroundColor: 'var(--color-bg)', outline: 'none' }}
            >
              <option value="" disabled>Select a station...</option>
              {stations.filter(s => s).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={typography.label}>Raw Field Report</label>
            <textarea
              rows={5}
              maxLength={500}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="ಮೆಜೆಸ್ಟಿಕ್ ಬಳಿ ವಾಹನ ಕೆಟ್ಟು ನಿಂತಿದೆ..."
              style={{
                padding: '12px',
                borderRadius: '6px',
                border: `1px solid ${colors.border}`,
                fontSize: '13px',
                fontFamily: typography.fontFamily,
                color: colors.textPrimary,
                backgroundColor: 'var(--color-bg)',
                outline: 'none',
                resize: 'vertical',
                lineHeight: '1.5'
              }}
            />
          </div>

          {/* Footer details under textarea */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px' }}>
            <span style={{ color: colors.textTertiary, fontFamily: typography.fontFamily }}>
              UTF-8 · English / Kannada / code-mixed
            </span>
            <span style={{ color: colors.textTertiary, fontFamily: 'monospace' }}>
              {characterCount} / 500
            </span>
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={!text.trim() || uiState === 'loading'}
            style={{
              ...buttons.primary,
              width: '100%',
              opacity: (!text.trim() || uiState === 'loading') ? 0.5 : 1,
              cursor: (!text.trim() || uiState === 'loading') ? 'not-allowed' : 'pointer'
            }}
          >
            Classify →
          </button>
        </form>
      </div>

      {/* Loading State */}
      {uiState === 'loading' && (
        <div style={{
          ...cards.base,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          {/* Shimmer line 1 */}
          <div style={{
            height: '14px',
            width: '25%',
            borderRadius: '4px',
            animation: 'sweep 1.2s linear infinite',
            backgroundImage: 'linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)',
            backgroundSize: '200% 100%'
          }} />
          {/* Shimmer line 2 */}
          <div style={{
            height: '16px',
            width: '60%',
            borderRadius: '4px',
            animation: 'sweep 1.2s linear infinite',
            backgroundImage: 'linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)',
            backgroundSize: '200% 100%'
          }} />
          <div style={{ height: '1px', backgroundColor: colors.border, margin: '4px 0' }} />
          {/* Shimmer line 3 */}
          <div style={{
            height: '50px',
            width: '100%',
            borderRadius: '4px',
            animation: 'sweep 1.2s linear infinite',
            backgroundImage: 'linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)',
            backgroundSize: '200% 100%'
          }} />
        </div>
      )}

      {/* Result Card */}
      {uiState === 'result' && result && (() => {
        const confPct = result.cause_confidence * 100;
        let confColor = '#DC2626'; // red
        if (confPct >= 80) confColor = colors.success; // green
        else if (confPct >= 60) confColor = colors.warning; // amber

        return (
          <div style={{ ...cards.base, animation: 'slideUp 200ms ease-out forwards' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {/* Left cause indicator */}
                <span style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  padding: '4px 10px',
                  borderRadius: '99px',
                  backgroundColor: `${causeColor}15`,
                  color: causeColor,
                  border: `1px solid ${causeColor}30`
                }}>
                  {result.event_cause.replace('_', ' ')}
                </span>

                {/* Right confidence score text */}
                <div style={{ ...typography.subtitle, fontSize: '11px', whiteSpace: 'nowrap' }}>
                  confidence: {result.cause_confidence?.toFixed(3)}
                </div>
              </div>

              {/* Confidence Meter Bar */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--color-border)', borderRadius: '99px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    backgroundColor: confColor,
                    width: `${confPct}%`
                  }} />
                </div>
                {/* Explainability Anchor */}
                <div style={{ fontSize: '11px', color: colors.textTertiary, fontFamily: typography.fontFamily, marginTop: '2px' }}>
                  Based on paraphrase-multilingual-mpnet-base-v2 embeddings · 6,683 training descriptions
                </div>
              </div>

              {/* Formatted JSON block */}
              <pre style={{
                backgroundColor: 'var(--color-bg)',
                border: `1px solid ${colors.border}`,
                borderRadius: '6px',
                padding: '12px',
                fontFamily: 'monospace',
                fontSize: '12px',
                color: colors.textPrimary,
                overflowX: 'auto',
                margin: 0
              }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          </div>
        );
      })()}

      {/* Example Prompts Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginTop: '4px',
        padding: '0 4px'
      }}>
        <span style={{ ...typography.label, fontSize: '11px', color: colors.textSecondary, textTransform: 'none', letterSpacing: 'normal' }}>
          Try examples
        </span>
        <button
          type="button"
          onClick={() => loadExample(examples.english)}
          style={{
            ...buttons.secondary,
            padding: '6px 12px',
            fontSize: '11px',
            borderRadius: '99px'
          }}
        >
          English sample
        </button>
        <button
          type="button"
          onClick={() => loadExample(examples.kannada)}
          style={{
            ...buttons.secondary,
            padding: '6px 12px',
            fontSize: '11px',
            borderRadius: '99px'
          }}
        >
          Kannada sample
        </button>
        <button
          type="button"
          onClick={() => loadExample(examples.codeMixed)}
          style={{
            ...buttons.secondary,
            padding: '6px 12px',
            fontSize: '11px',
            borderRadius: '99px'
          }}
        >
          CodeMixed sample
        </button>
      </div>

    </div>
  );
}

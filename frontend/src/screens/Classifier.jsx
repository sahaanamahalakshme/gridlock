import { useState } from 'react';
import { colors, typography, cards, buttons } from '../styles/globals';

export default function Classifier() {
  const [text, setText] = useState('');
  const [uiState, setUiState] = useState('default'); // 'default' | 'loading' | 'result'
  const [result, setResult] = useState(null);

  const characterCount = text.length;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setUiState('loading');
    setResult(null);

    try {
      const response = await fetch('/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: text })
      });
      if (!response.ok) throw new Error('API failed');
      const data = await response.json();
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
                {/* Left cause & routing indicator */}
                <div style={{ display: 'flex', gap: '8px' }}>
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

                  {result.routing && (
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      padding: '4px 10px',
                      borderRadius: '99px',
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      color: 'rgb(37, 99, 235)',
                      border: '1px solid rgba(59, 130, 246, 0.3)'
                    }}>
                      Routing: {result.routing.routing_agency} {result.routing.is_ambiguous ? '*' : ''}
                    </span>
                  )}
                </div>

                {/* Right confidence score text */}
                <div style={{ ...typography.subtitle, fontSize: '11px', whiteSpace: 'nowrap', fontWeight: 600 }}>
                  MATCH CONFIDENCE: {confPct.toFixed(1)}%
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
                  Based on paraphrase-multilingual-MiniLM-L12-v2 embeddings · 6,813 training descriptions
                </div>
              </div>

              {/* Descriptive Output Block */}
              <div style={{
                backgroundColor: 'var(--color-bg)',
                border: `1px solid ${colors.border}`,
                borderRadius: '6px',
                padding: '16px',
                fontSize: '13px',
                color: colors.textPrimary,
                margin: 0,
                lineHeight: '1.6'
              }}>
                The model classified this report as <strong>{result.event_cause.replace('_', ' ')}</strong> with a confidence score of <strong>{(result.cause_confidence * 100).toFixed(1)}%</strong>. 
                The estimated severity of the incident is <strong>{result.severity}</strong> ({(result.severity_confidence * 100).toFixed(1)}% confidence). 
                {result.routing && (
                  <> Based on civic routing rules, this incident should be assigned to the <strong>{result.routing.routing_agency.toUpperCase()}</strong>{result.routing.is_ambiguous ? ' (Warning: Ambiguous routing matched)' : ''}.</>
                )}
                
                {result.top5_causes && result.top5_causes.length > 1 && (
                  <div style={{ marginTop: '12px', borderTop: `1px solid ${colors.border}`, paddingTop: '12px' }}>
                    <div style={{ fontSize: '11px', color: colors.textTertiary, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Alternative classifications</div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {result.top5_causes.slice(1, 4).map((c, i) => (
                        <span key={i} style={{ fontSize: '11px', backgroundColor: 'var(--color-card-bg)', border: `1px solid ${colors.border}`, padding: '2px 8px', borderRadius: '99px', color: colors.textSecondary }}>
                          {c.label.replace('_', ' ')} ({(c.confidence * 100).toFixed(1)}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
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

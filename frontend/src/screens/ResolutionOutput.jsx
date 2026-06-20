import { useState, useEffect, useRef } from "react";
import { colors, typography, cards } from "../styles/globals";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function ResolutionOutput({ predictionData }) {
  const [showRawOutput, setShowRawOutput] = useState(false);
  const [data, setData] = useState(null);

  const [activeStage, setActiveStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (predictionData) {
      setData({
        predicted_minutes: predictionData.resolution_estimate?.predicted_minutes || 0,
        confidence_band: predictionData.resolution_estimate?.confidence_band || "N/A",
        manpower_tier: predictionData.resolution_estimate?.manpower_tier || "N/A",
        explanation:
          predictionData.resolution_estimate?.explanation || "No explanation",
        similar_events: (predictionData.precedent?.matches || [])
          .slice(0, 3)
          .map((m) => ({
            name: m.description,
            corridor: m.corridor,
            duration: m.duration_minutes,
          })),
        total_matches: predictionData.precedent?.total_matches || 0,
        temporal: predictionData.context?.temporal,
        hotspot: predictionData.context?.hotspot,
        raw_json: predictionData,
      });
    } else {
      setData(null);
    }
  }, [predictionData]);

  useEffect(() => {
    if (isPlaying) {
      if (activeStage >= 5) {
        setIsPlaying(false);
        return;
      }
      timerRef.current = setInterval(() => {
        setActiveStage((s) => {
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
    { label: "Event reported", pct: 0 },
    { label: "Officers dispatched", pct: 0.15 },
    { label: "Diversion active", pct: 0.4 },
    { label: "Traffic normalising", pct: 0.75 },
    { label: "Road cleared", pct: 1.0 },
  ];

  if (!data) {
    return (
      <div
        style={{
          padding: "80px 40px",
          textAlign: "center",
          color: "var(--color-text-secondary)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "16px",
        }}
      >
        <span style={{ fontSize: "32px" }}>⏱️</span>
        <div style={{ ...typography.header, fontSize: "18px" }}>
          No event predicted yet
        </div>
        <div style={{ ...typography.body, maxWidth: "340px", lineHeight: "1.5" }}>
          Predict an event to see its estimated resolution timeline, manpower
          requirements, and historical precedent.
        </div>
      </div>
    );
  }

  const hoursFromStart = Math.round((data.predicted_minutes / 60) * 10) / 10;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div>
        <h1 style={{ ...typography.header, margin: 0, fontSize: "16px" }}>
          Resolution Output
        </h1>
        <p style={{ ...typography.subtitle, margin: 0, marginTop: "2px" }}>
          Model output for a classified or planned event
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "40fr 60fr",
          gap: "16px",
          alignItems: "start",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: "4px" }}>
              Predicted Clearance
            </div>

            <div
              style={{
                fontFamily: typography.fontFamily,
                fontSize: "20px",
                fontWeight: "400",
                color: colors.textPrimary,
              }}
            >
              {data.predicted_minutes} min
            </div>
            <div
              style={{
                ...typography.subtitle,
                marginTop: "2px",
                marginBottom: "12px",
              }}
            >
              ≈ {hoursFromStart} hours from event start
            </div>

            <div
              style={{
                height: "4px",
                backgroundColor: "var(--color-border)",
                borderRadius: "99px",
                width: "100%",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: "50%",
                  backgroundColor: colors.warning,
                  borderRadius: "99px",
                }}
              />
            </div>
          </div>

          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: "4px" }}>
              Confidence Band
            </div>
            <div
              style={{
                ...typography.value,
                fontSize: "18px",
                color: colors.success,
                fontWeight: "600",
              }}
            >
              {data.confidence_band}
            </div>
            <div style={{ ...typography.subtitle, marginTop: "4px" }}>
              Based on {data.total_matches} similar historical events
            </div>
          </div>

          <div style={cards.base}>
            <div style={{ ...typography.label, marginBottom: "4px" }}>
              Manpower Tier
            </div>
            <div
              style={{
                ...typography.value,
                fontSize: "18px",
                color: colors.warning,
                fontWeight: "600",
              }}
            >
              {data.manpower_tier}
            </div>
            <div style={{ ...typography.subtitle, marginTop: "4px" }}>
              Resource deployment recommended
            </div>
          </div>

          {data.temporal && (
            <div style={cards.base}>
              <div style={{ ...typography.label, marginBottom: "4px" }}>
                Traffic Context
              </div>
              <div
                style={{
                  ...typography.value,
                  fontSize: "18px",
                  color: data.temporal.is_spike ? "#DC2626" : colors.success,
                  fontWeight: "600",
                }}
              >
                {data.temporal.is_spike
                  ? `${data.temporal.spike_ratio}× normal`
                  : "Normal"}
              </div>
              <div style={{ ...typography.subtitle, marginTop: "4px" }}>
                {new Date().toLocaleDateString("en-US", { weekday: "short" })}{" "}
                {String(data.temporal.hour).padStart(2, "0")}:00 · baseline{" "}
                {data.temporal.baseline_avg} events/hr
              </div>
            </div>
          )}
        </div>

        <div
          style={{
            ...cards.base,
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {data.hotspot?.is_hotspot && (
            <div
              style={{
                backgroundColor: "#FEF2F2",
                border: "1px solid #FECACA",
                padding: "16px",
                borderRadius: "6px",
                color: "#991B1B",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "8px",
                }}
              >
                <span style={{ fontSize: "16px" }}>⚠️</span>
                <strong
                  style={{
                    fontSize: "14px",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Chronic Location: {data.hotspot.hotspot_tier} Risk
                </strong>
              </div>
              <div style={{ fontSize: "13px", lineHeight: "1.5" }}>
                This junction has recorded{" "}
                <strong>{data.hotspot.historical_count} prior incidents</strong>
                , predominantly{" "}
                <strong>
                  {data.hotspot.dominant_cause?.replace("_", " ")}
                </strong>
                .
                {data.hotspot.route_to !== "Traffic Police"
                  ? ` Civic routing recommends assigning to ${data.hotspot.route_to}.`
                  : ""}
              </div>
            </div>
          )}

          <div>
            <div style={{ ...typography.label, marginBottom: "8px" }}>
              Explanation
            </div>
            <div
              style={{
                borderLeft: `3px solid ${colors.accent}`,
                backgroundColor: "var(--color-bg)",
                padding: "12px",
                borderRadius: "0 6px 6px 0",
              }}
            >
              <p style={{ ...typography.body, margin: 0 }}>
                {data.explanation}
              </p>
            </div>
          </div>

          <div>
            <div style={{ ...typography.label, marginBottom: "8px" }}>
              Similar Historical Events
            </div>
            {data.similar_events.length > 0 ? (
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  marginBottom: "8px",
                }}
              >
                <tbody>
                  {data.similar_events.map((evt, idx) => (
                    <tr
                      key={idx}
                      style={{
                        borderBottom: `1px solid ${colors.border}`,
                        transition: "background-color 150ms ease",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.backgroundColor = "#F9FAFB")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.backgroundColor = "transparent")
                      }
                    >
                      <td
                        style={{
                          ...typography.body,
                          padding: "8px 4px",
                          fontWeight: "500",
                        }}
                      >
                        {evt.name || "Event"}
                      </td>
                      <td
                        style={{
                          ...typography.body,
                          padding: "8px 4px",
                          color: colors.textSecondary,
                        }}
                      >
                        {evt.corridor}
                      </td>
                      <td
                        style={{
                          ...typography.body,
                          padding: "8px 4px",
                          textAlign: "right",
                        }}
                      >
                        {evt.duration} min
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div
                style={{
                  ...typography.body,
                  color: colors.textSecondary,
                  marginBottom: "8px",
                }}
              >
                No similar events found.
              </div>
            )}
            <div
              style={{
                fontSize: "11px",
                color: colors.textTertiary,
                fontFamily: typography.fontFamily,
              }}
            >
              Retrieved from ASTRAM memory store
            </div>
          </div>

          <div>
            <div style={{ ...typography.label, marginBottom: "8px" }}>
              Severity
            </div>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "600",
                  padding: "4px 10px",
                  borderRadius: "99px",
                  backgroundColor: "#FEF2F2",
                  color: "#DC2626",
                  border: "1px solid #FECACA",
                }}
              >
                Priority Event
              </span>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "600",
                  padding: "4px 10px",
                  borderRadius: "99px",
                  backgroundColor: "#FFFBEB",
                  color: "#D97706",
                  border: "1px solid #FEF3C7",
                }}
              >
                Dynamic classification
              </span>
            </div>
          </div>

          <div
            style={{
              marginTop: "8px",
              borderTop: `1px solid ${colors.border}`,
              paddingTop: "16px",
            }}
          >
            <div
              style={{
                ...typography.body,
                fontSize: "13px",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
              onClick={() => setShowRawOutput(!showRawOutput)}
            >
              Raw model output {showRawOutput ? "↑" : "↓"}
            </div>
            {showRawOutput && (
              <pre
                style={{
                  marginTop: "12px",
                  backgroundColor: "var(--color-bg)",
                  border: `1px solid ${colors.border}`,
                  borderRadius: "6px",
                  padding: "12px",
                  fontFamily: "monospace",
                  fontSize: "12px",
                  color: colors.textPrimary,
                  overflowX: "auto",
                  margin: 0,
                }}
              >
                {JSON.stringify(data.raw_json, null, 2)}
              </pre>
            )}
          </div>
        </div>
      </div>

      <div style={{ ...cards.base, marginTop: "8px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "24px",
          }}
        >
          <h2 style={{ ...typography.label, fontSize: "13px", margin: 0 }}>
            Resolution Simulation Timeline
          </h2>
          <button
            onClick={() => {
              if (activeStage >= 5) setActiveStage(0);
              setIsPlaying(!isPlaying);
            }}
            style={{
              backgroundColor: "var(--color-card-bg)",
              color: colors.textPrimary,
              border: `1px solid ${colors.border}`,
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "12px",
              fontWeight: 500,
              cursor: "pointer",
              transition:
                "all 150ms ease, background-color 150ms ease, color 150ms ease",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            {isPlaying
              ? "⏸ Pause"
              : activeStage >= 5
                ? "↻ Replay"
                : "▶ Simulate"}
          </button>
        </div>

        <div
          style={{
            display: "flex",
            position: "relative",
            justifyContent: "space-between",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "10px",
              left: "20px",
              right: "20px",
              height: "2px",
              backgroundColor: "var(--color-border)",
              zIndex: 0,
            }}
          />

          <div
            style={{
              position: "absolute",
              top: "10px",
              left: "20px",
              width: `${Math.min(100, Math.max(0, activeStage / (stages.length - 1)) * 100)}%`,
              height: "2px",
              backgroundColor: colors.accent,
              zIndex: 1,
              transition: "width 300ms ease",
            }}
          />

          {stages.map((stage, idx) => {
            const isCompleted = activeStage > idx;
            const isCurrent = activeStage === idx;

            let circleBg = "var(--color-card-bg)";
            let circleBorder = `2px solid var(--color-border)`;
            let icon = null;

            if (isCompleted) {
              circleBg = colors.accent;
              circleBorder = `2px solid ${colors.accent}`;
              icon = (
                <span
                  style={{
                    color: "#FFFFFF",
                    fontSize: "10px",
                    fontWeight: "bold",
                  }}
                >
                  ✓
                </span>
              );
            } else if (isCurrent) {
              circleBg = colors.accent;
              circleBorder = `2px solid ${colors.accent}`;
            }

            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  zIndex: 2,
                  width: "120px",
                }}
              >
                <div
                  style={{
                    width: "20px",
                    height: "20px",
                    borderRadius: "50%",
                    backgroundColor: circleBg,
                    border: circleBorder,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 300ms ease",
                    boxSizing: "border-box",
                  }}
                >
                  {icon}
                </div>
                <div
                  style={{
                    ...typography.body,
                    fontSize: "12px",
                    marginTop: "8px",
                    fontWeight: isCurrent || isCompleted ? 600 : 400,
                    color:
                      isCurrent || isCompleted
                        ? colors.textPrimary
                        : colors.textSecondary,
                    textAlign: "center",
                  }}
                >
                  {stage.label}
                </div>
                <div
                  style={{
                    ...typography.subtitle,
                    fontSize: "11px",
                    marginTop: "4px",
                  }}
                >
                  +{Math.round(data.predicted_minutes * stage.pct)} min
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

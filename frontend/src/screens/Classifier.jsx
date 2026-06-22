import { useState } from "react";
import { colors, typography, cards, buttons } from "../styles/globals";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function Classifier() {
  const [text, setText] = useState("");
  const [policeStation, setPoliceStation] = useState("");
  const [uiState, setUiState] = useState("default");
  const [result, setResult] = useState(null);

  const characterCount = text.length;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setUiState("loading");
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: text,
          police_station: policeStation,
        }),
      });
      const data = await res.json();
      setResult(data);
      setUiState("result");
    } catch (err) {
      console.error(err);
      setUiState("default");
    }
  };

  const loadExample = (exampleText) => {
    setText(exampleText);

    setUiState("default");
    setResult(null);
  };

  const examples = {
    english:
      "Accident reported near Hebbal flyover between a car and a two-wheeler, heavy congestion building up.",
    kannada:
      "ಮೆಜೆಸ್ಟಿಕ್ ಬಳಿ ಬಿಎಂಟಿಸಿ ಬಸ್ ಕೆಟ್ಟು ನಿಂತಿದ್ದರಿಂದ ಟ್ರಾಫಿಕ್ ಜಾಮ್ ಆಗಿದೆ.",
    codeMixed:
      "Silk Board junction hatra vehicle breakdown agide, please clear it immediately.",
  };

  const stations = [
    "",
    "Cubbon Park",
    "High Grounds",
    "Ulsoor",
    "Shivajinagar",
    "Commercial Street",
    "Koramangala",
    "HSR Layout",
    "Indiranagar",
    "Madivala",
    "Silk Board",
    "Whitefield",
    "Bellandur",
    "Hebbal",
    "Jayanagar",
    "JP Nagar",
  ];

  const causeColor = result
    ? colors.causes[result.event_cause] || colors.causes.others
    : colors.textSecondary;

  return (
    <div
      style={{
        maxWidth: "680px",
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      <div>
        <h1 style={{ ...typography.header, margin: 0, fontSize: "16px" }}>
          Field Report Classifier
        </h1>
        <p style={{ ...typography.subtitle, margin: 0, marginTop: "2px" }}>
          Paste a raw report in English or Kannada
        </p>
      </div>

      <div style={cards.base}>
        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "14px" }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={typography.label}>Police Station (Optional)</label>
            <select
              value={policeStation}
              onChange={(e) => setPoliceStation(e.target.value)}
              style={{
                padding: "8px 12px",
                borderRadius: "6px",
                border: `1px solid ${colors.border}`,
                fontSize: "13px",
                fontFamily: typography.fontFamily,
                color: colors.textPrimary,
                backgroundColor: "var(--color-bg)",
                outline: "none",
              }}
            >
              <option value="" disabled>
                Select a station...
              </option>
              {stations
                .filter((s) => s)
                .map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
            </select>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={typography.label}>Raw Field Report</label>
            <textarea
              rows={5}
              maxLength={500}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="ಮೆಜೆಸ್ಟಿಕ್ ಬಳಿ ವಾಹನ ಕೆಟ್ಟು ನಿಂತಿದೆ..."
              style={{
                padding: "12px",
                borderRadius: "6px",
                border: `1px solid ${colors.border}`,
                fontSize: "13px",
                fontFamily: typography.fontFamily,
                color: colors.textPrimary,
                backgroundColor: "var(--color-bg)",
                outline: "none",
                resize: "vertical",
                lineHeight: "1.5",
              }}
            />
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: "11px",
            }}
          >
            <span
              style={{
                color: colors.textTertiary,
                fontFamily: typography.fontFamily,
              }}
            >
              UTF-8 · English / Kannada / code-mixed
            </span>
            <span
              style={{ color: colors.textTertiary, fontFamily: "monospace" }}
            >
              {characterCount} / 500
            </span>
          </div>

          <button
            type="submit"
            disabled={!text.trim() || uiState === "loading"}
            style={{
              ...buttons.primary,
              width: "100%",
              opacity: !text.trim() || uiState === "loading" ? 0.5 : 1,
              cursor:
                !text.trim() || uiState === "loading"
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            Classify →
          </button>
        </form>
      </div>

      {uiState === "loading" && (
        <div
          style={{
            ...cards.base,
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          <div
            style={{
              height: "14px",
              width: "25%",
              borderRadius: "4px",
              animation: "sweep 1.2s linear infinite",
              backgroundImage:
                "linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)",
              backgroundSize: "200% 100%",
            }}
          />

          <div
            style={{
              height: "16px",
              width: "60%",
              borderRadius: "4px",
              animation: "sweep 1.2s linear infinite",
              backgroundImage:
                "linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)",
              backgroundSize: "200% 100%",
            }}
          />
          <div
            style={{
              height: "1px",
              backgroundColor: colors.border,
              margin: "4px 0",
            }}
          />

          <div
            style={{
              height: "50px",
              width: "100%",
              borderRadius: "4px",
              animation: "sweep 1.2s linear infinite",
              backgroundImage:
                "linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)",
              backgroundSize: "200% 100%",
            }}
          />
        </div>
      )}

      {uiState === "result" &&
        result &&
        (() => {
          const confPct = result.cause_confidence * 100;
          let confColor = "#DC2626";
          if (confPct >= 80) confColor = colors.success;
          else if (confPct >= 60) confColor = colors.warning;

          return (
            <div
              style={{
                ...cards.base,
                animation: "slideUp 200ms ease-out forwards",
              }}
            >
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      padding: "4px 10px",
                      borderRadius: "99px",
                      backgroundColor: `${causeColor}15`,
                      color: causeColor,
                      border: `1px solid ${causeColor}30`,
                    }}
                  >
                    {result.event_cause.replace("_", " ")}
                  </span>

                  <div
                    style={{
                      ...typography.subtitle,
                      fontSize: "11px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    confidence: {result.cause_confidence?.toFixed(3)}
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                  }}
                >
                  <div
                    style={{
                      width: "100%",
                      height: "4px",
                      backgroundColor: "var(--color-border)",
                      borderRadius: "99px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        backgroundColor: confColor,
                        width: `${confPct}%`,
                      }}
                    />
                  </div>

                  <div
                    style={{
                      fontSize: "11px",
                      color: colors.textTertiary,
                      fontFamily: typography.fontFamily,
                      marginTop: "2px",
                    }}
                  >
                    Based on paraphrase-multilingual-mpnet-base-v2 embeddings ·
                    6,683 training descriptions
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: "var(--color-bg)",
                    border: `1px solid ${colors.border}`,
                    borderRadius: "6px",
                    padding: "16px",
                    fontSize: "14px",
                    color: colors.textPrimary,
                    margin: 0,
                    lineHeight: "1.6",
                  }}
                >
                  <p style={{ margin: 0 }}>
                    This report was classified similar to <strong>{result.event_cause?.replace("_", " ")}</strong> ({(result.cause_confidence * 100).toFixed(1)}% confidence).
                    {result.severity && (
                      <> The severity is estimated to be <strong>{result.severity}</strong> ({(result.severity_confidence * 100).toFixed(1)}% confidence).</>
                    )}
                    {result.routing && (
                      <> Based on these factors, the issue will be routed to the <strong>{result.routing.routing_agency?.replace("_", " ")}</strong> department{result.routing.is_ambiguous ? " (requires manual review due to ambiguity)" : ""}.</>
                    )}
                  </p>
                </div>
              </div>
            </div>
          );
        })()}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginTop: "4px",
          padding: "0 4px",
        }}
      >
        <span
          style={{
            ...typography.label,
            fontSize: "11px",
            color: colors.textSecondary,
            textTransform: "none",
            letterSpacing: "normal",
          }}
        >
          Try examples
        </span>
        <button
          type="button"
          onClick={() => loadExample(examples.english)}
          style={{
            ...buttons.secondary,
            padding: "6px 12px",
            fontSize: "11px",
            borderRadius: "99px",
          }}
        >
          English sample
        </button>
        <button
          type="button"
          onClick={() => loadExample(examples.kannada)}
          style={{
            ...buttons.secondary,
            padding: "6px 12px",
            fontSize: "11px",
            borderRadius: "99px",
          }}
        >
          Kannada sample
        </button>
        <button
          type="button"
          onClick={() => loadExample(examples.codeMixed)}
          style={{
            ...buttons.secondary,
            padding: "6px 12px",
            fontSize: "11px",
            borderRadius: "99px",
          }}
        >
          CodeMixed sample
        </button>
      </div>
    </div>
  );
}

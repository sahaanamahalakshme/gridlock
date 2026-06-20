import { useState, useEffect, useRef } from "react";
import { colors, typography } from "./styles/globals";

import HotspotMap from "./screens/HotspotMap";
import PredictEvent from "./screens/PredictEvent";
import Classifier from "./screens/Classifier";
import ResolutionOutput from "./screens/ResolutionOutput";
import SimulationPage from "./screens/SimulationPage";

const SunIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="5"></circle>
    <line x1="12" y1="1" x2="12" y2="3"></line>
    <line x1="12" y1="21" x2="12" y2="23"></line>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
    <line x1="1" y1="12" x2="3" y2="12"></line>
    <line x1="21" y1="12" x2="23" y2="12"></line>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
  </svg>
);

const MoonIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
  </svg>
);

const TargetIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const ZapIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

const MessageSquareIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const ClockIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const MapPinIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
    <circle cx="12" cy="10" r="3" />
  </svg>
);

const NAV_ITEMS = [
  { id: "hotspot", label: "Hotspot Map", icon: <TargetIcon /> },
  { id: "predict", label: "Predict Event", icon: <ZapIcon /> },
  { id: "classifier", label: "Classifier", icon: <MessageSquareIcon /> },
  { id: "resolution", label: "Resolution Output", icon: <ClockIcon /> },
  { id: "simulation", label: "Simulate", icon: <MapPinIcon /> },
];

export default function App() {
  const [activeView, setActiveView] = useState("hotspot");
  const [hoveredNav, setHoveredNav] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [predictFill, setPredictFill] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const searchInputRef = useRef(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isConnecting, setIsConnecting] = useState(true);

  useEffect(() => {
    const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    fetch(`${API_BASE}/health`)
      .then(() => setIsConnecting(false))
      .catch((err) => {
        console.error("Health check failed:", err);
        setTimeout(() => setIsConnecting(false), 3000);
      });
  }, []);

  if (isConnecting) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: colors.bg,
          fontFamily: typography.fontFamily,
          color: colors.textPrimary,
        }}
      >
        <div
          style={{
            marginBottom: "20px",
            width: "40px",
            height: "40px",
            borderRadius: "50%",
            border: `3px solid ${colors.border}`,
            borderTopColor: colors.accent,
            animation: "spin 1s linear infinite",
          }}
        ></div>
        <h2 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "8px" }}>
          Connecting to DRISHTI...
        </h2>
        <p
          style={{
            fontSize: "14px",
            color: colors.textSecondary,
            maxWidth: "300px",
            textAlign: "center",
          }}
        >
          Waking up backend services. This may take 30-60 seconds on a cold start.
        </p>
        <style>
          {`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}
        </style>
      </div>
    );
  }
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add("dark");
    } else {
      document.body.classList.remove("dark");
    }
  }, [isDarkMode]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
      if (e.key === "Escape") {
        setSearchQuery("");
        searchInputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const renderContent = () => {
    switch (activeView) {
      case "hotspot":
        return (
          <HotspotMap
            searchQuery={searchQuery}
            onPredictClick={(data) => {
              setPredictFill(data);
              setActiveView("predict");
            }}
          />
        );
      case "predict":
        return (
          <PredictEvent
            initialData={predictFill}
            onPredictionSuccess={setPredictionData}
          />
        );
      case "classifier":
        return <Classifier />;
      case "resolution":
        return <ResolutionOutput predictionData={predictionData} />;
      case "simulation":
        return <SimulationPage />;
      default:
        return (
          <HotspotMap
            searchQuery={searchQuery}
            onPredictClick={(data) => {
              setPredictFill(data);
              setActiveView("predict");
            }}
          />
        );
    }
  };

  return (
    <div
      style={{
        fontFamily: typography.fontFamily,
        color: colors.textPrimary,
        backgroundColor: colors.bg,
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: "48px",
          backgroundColor: "var(--color-card-bg)",
          borderBottom: `1px solid ${colors.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          transition: "background-color 150ms ease",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "13px", fontWeight: "600" }}>DRISHTI</span>
          <span style={{ color: colors.border }}>|</span>
          <span style={{ fontSize: "13px", color: colors.textSecondary }}>
            Resolution Intelligence
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span
            style={{
              fontSize: "11px",
              textTransform: "uppercase",
              color: colors.textSecondary,
              backgroundColor: "var(--color-gray-bg)",
              border: `1px solid ${colors.border}`,
              borderRadius: "99px",
              padding: "2px 8px",
              letterSpacing: "0.05em",
            }}
          >
            B-TRAC · ASTRAM
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: colors.success,
              }}
            ></span>
            <span style={{ fontSize: "11px", color: colors.textSecondary }}>
              Model active
            </span>
          </div>
          <div
            style={{
              width: "1px",
              height: "16px",
              backgroundColor: colors.border,
              margin: "0 4px",
            }}
          />
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              color: colors.textSecondary,
              padding: "4px",
              borderRadius: "4px",
            }}
            title={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {isDarkMode ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", marginTop: "48px", flexGrow: 1 }}>
        <div
          style={{
            width: "200px",
            backgroundColor: "var(--color-card-bg)",
            borderRight: `1px solid ${colors.border}`,
            position: "fixed",
            top: "48px",
            bottom: 0,
            left: 0,
            display: "flex",
            flexDirection: "column",
            paddingTop: "16px",
            zIndex: 90,
            transition: "background-color 150ms ease",
          }}
        >
          <nav style={{ flexGrow: 1 }}>
            {NAV_ITEMS.map((item) => {
              const isActive = activeView === item.id;
              const isHovered = hoveredNav === item.id;

              const bg = isActive
                ? "var(--color-active-bg)"
                : isHovered
                  ? "var(--color-hover-bg)"
                  : "transparent";
              const fg = isActive ? colors.accent : colors.textPrimary;
              const borderLeft = isActive
                ? `2px solid ${colors.accent}`
                : "2px solid transparent";
              const matchesSearch =
                searchQuery.trim() &&
                item.label.toLowerCase().includes(searchQuery.toLowerCase());

              return (
                <div
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  onMouseEnter={() => setHoveredNav(item.id)}
                  onMouseLeave={() => setHoveredNav(null)}
                  style={{
                    height: "36px",
                    display: "flex",
                    alignItems: "center",
                    padding: "0 16px",
                    gap: "12px",
                    fontSize: "13px",
                    cursor: "pointer",
                    backgroundColor: bg,
                    color: fg,
                    borderLeft: borderLeft,
                    transition: "all 150ms ease",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      opacity: isActive ? 1 : 0.7,
                    }}
                  >
                    {item.icon}
                  </div>
                  <span style={{ flexGrow: 1 }}>{item.label}</span>
                  {matchesSearch && (
                    <span
                      style={{
                        width: "6px",
                        height: "6px",
                        borderRadius: "50%",
                        backgroundColor: colors.accent,
                      }}
                    />
                  )}
                </div>
              );
            })}
          </nav>
          <div
            style={{
              padding: "16px",
              fontSize: "11px",
              color: colors.textTertiary,
            }}
          >
            v0.1 · Prototype
          </div>
        </div>

        <div style={{ marginLeft: "200px", width: "100%" }}>
          <div
            style={{ padding: "24px", maxWidth: "1100px", margin: "0 auto" }}
          >
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
}

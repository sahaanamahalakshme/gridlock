import React, { useEffect, useState } from "react";
import { colors, typography, cards } from "../styles/globals";
import { CAUSE_TOTALS, HOTSPOT_JUNCTIONS } from "../mockData";

export default function LandingPage({ setActiveView }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const mapContainer = React.useRef(null);
  const mapRef = React.useRef(null);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current || !window.maplibregl) return;

    const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

    fetch(`${API_BASE}/events/hotspot`)
      .then((res) => res.json())
      .then((data) => {
        const map = new window.maplibregl.Map({
          container: mapContainer.current,
          style: {
            version: 8,
            sources: {
              osm: {
                type: "raster",
                tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                tileSize: 256,
              },
            },
            layers: [{ id: "osm", type: "raster", source: "osm", minzoom: 0, maxzoom: 19 }],
          },
          center: [77.59, 12.97],
          zoom: 10,
          interactive: false,
        });

        map.on("load", () => {
          data.junctions.forEach((j) => {
            if (j.count > 10) {
              const el = document.createElement("div");
              el.style.width = "10px";
              el.style.height = "10px";
              el.style.borderRadius = "50%";
              el.style.backgroundColor = colors.causes[j.dominant_cause] || colors.causes.others;
              el.style.boxShadow = "0 0 10px " + el.style.backgroundColor;
              new window.maplibregl.Marker({ element: el }).setLngLat([j.lng, j.lat]).addTo(map);
            }
          });
        });
        mapRef.current = map;
      })
      .catch(console.error);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Mock recent events for the Live Events widget
  const liveEvents = [
    { cause: "Vehicle Breakdown", location: "Mekhri Circle", time: "2 mins ago", impact: "High Impact", impactColor: colors.danger, iconColor: colors.causes.vehicle_breakdown },
    { cause: "Road Work", location: "Kanakapura Road", time: "5 mins ago", impact: "Medium Impact", impactColor: colors.warning, iconColor: colors.causes.construction },
    { cause: "Water Logging", location: "Sarjapur Road", time: "7 mins ago", impact: "Low Impact", impactColor: colors.accent, iconColor: colors.causes.water_logging },
    { cause: "Minor Accident", location: "Outer Ring Road", time: "9 mins ago", impact: "Low Impact", impactColor: colors.accent, iconColor: colors.causes.accident },
  ];

  const totalCauses = Object.values(CAUSE_TOTALS).reduce((a, b) => a + b, 0);

  return (
    <div className="landing-page w-full max-w-7xl mx-auto pb-16 animate-fade-in">
      {/* Hero Section */}
      <div className="flex flex-col lg:flex-row gap-8 lg:gap-16 items-center pt-8 pb-12">
        <div className="w-full lg:w-1/2 flex flex-col items-start gap-6">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-blue-600 bg-blue-50 dark:bg-blue-900/30 px-3 py-1 rounded-full">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            DYNAMIC · REAL-TIME · PREDICTIVE
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-tight" style={{ color: "var(--color-text-primary)" }}>
            See Traffic <br/>
            <span className="text-blue-600">Before</span> <span style={{ color: "var(--color-text-primary)" }}>It Happens.</span>
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 leading-relaxed max-w-lg">
            DRISHTI transforms unstructured traffic reports into actionable intelligence predicting disruptions, uncovering patterns, and empowering Bengaluru to move from reacting to <span className="text-blue-600 font-medium">preventing</span>.
          </p>
          <div className="flex items-center gap-4 mt-2">
            <button 
              onClick={() => setActiveView("hotspot")}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-blue-600/20"
            >
              Explore DRISHTI
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
            <button 
              onClick={() => setActiveView("simulation")}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
            >
              How It Works
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M10 8l6 4-6 4V8z"/></svg>
            </button>
          </div>
        </div>

        <div className="w-full lg:w-1/2 relative min-h-[400px] bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm flex items-center justify-center p-4">
            {/* Map Placeholder Graphic */}
            <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]" style={{ backgroundImage: "radial-gradient(#000 1px, transparent 1px)", backgroundSize: "20px 20px" }}></div>
            
            <div className="relative w-full h-full min-h-[350px]">
              {/* Nodes and Lines */}
              <svg className="absolute inset-0 w-full h-full stroke-gray-300 dark:stroke-gray-600" style={{strokeWidth: 1.5, opacity: 0.5}}>
                <path d="M50 150 Q 150 100 250 200 T 450 150" fill="none" />
                <path d="M100 50 Q 200 250 350 200 T 450 300" fill="none" />
                <path d="M250 200 Q 300 100 400 50" fill="none" className="stroke-blue-400" strokeWidth="2" strokeDasharray="4 4" />
              </svg>

              {/* Pulsing Hotspots */}
              <div className="absolute top-[30%] left-[25%] flex items-center justify-center">
                <div className="absolute w-24 h-24 bg-red-500 rounded-full opacity-10 animate-ping"></div>
                <div className="absolute w-12 h-12 bg-red-500 rounded-full opacity-20"></div>
                <div className="w-3 h-3 bg-red-500 rounded-full z-10 shadow-[0_0_10px_rgba(239,68,68,0.8)]"></div>
              </div>
              <div className="absolute top-[45%] left-[65%] flex items-center justify-center">
                <div className="absolute w-32 h-32 bg-red-500 rounded-full opacity-10 animate-ping" style={{animationDelay: '1s'}}></div>
                <div className="absolute w-16 h-16 bg-red-500 rounded-full opacity-20"></div>
                <div className="w-4 h-4 bg-red-500 rounded-full z-10 shadow-[0_0_10px_rgba(239,68,68,0.8)]"></div>
              </div>

              {/* Tooltip 1 */}
              <div className="absolute top-[10%] left-[10%] bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700 rounded-xl p-3 z-20 flex flex-col gap-1 w-48 animate-slide-up hover:scale-105 transition-transform" style={{animationDelay: '0.2s'}}>
                <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Predicted Congestion</span>
                <span className="text-blue-600 font-semibold text-lg">21 mins</span>
                <span className="text-xs text-gray-600 dark:text-gray-300">Mekhri Circle</span>
              </div>

              {/* Tooltip 2 */}
              <div className="absolute bottom-[20%] left-[50%] bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700 rounded-xl p-3 z-20 flex flex-col gap-1 w-48 animate-slide-up hover:scale-105 transition-transform" style={{animationDelay: '0.4s'}}>
                <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Incident Detected</span>
                <span className="text-gray-900 dark:text-white font-semibold text-sm">Vehicle Breakdown</span>
                <span className="text-xs text-gray-600 dark:text-gray-300">Silk Board Junction</span>
              </div>

              {/* Tooltip 3 */}
              <div className="absolute top-[15%] right-[5%] bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700 rounded-xl p-3 z-20 flex flex-col gap-1 w-48 animate-slide-up hover:scale-105 transition-transform" style={{animationDelay: '0.6s'}}>
                <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Chronic Hotspot</span>
                <span className="text-red-600 font-semibold text-sm">High Impact</span>
                <span className="text-xs text-gray-600 dark:text-gray-300">Old Madras Road</span>
              </div>
            </div>
        </div>
      </div>

      {/* Stats Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 py-6 border-y border-gray-200 dark:border-gray-800 mb-10 bg-gray-50/50 dark:bg-gray-900/20 px-8 rounded-2xl">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center text-blue-600">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">100</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Total Junctions</div>
          </div>
        </div>
        <div className="hidden md:block w-px h-12 bg-gray-200 dark:bg-gray-700"></div>
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center text-red-600">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">85</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Chronic Locations</div>
          </div>
        </div>
        <div className="hidden md:block w-px h-12 bg-gray-200 dark:bg-gray-700"></div>
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/50 flex items-center justify-center text-green-600">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">6,303</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Events Analyzed</div>
          </div>
        </div>
        <div className="hidden md:block w-px h-12 bg-gray-200 dark:bg-gray-700"></div>
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center text-purple-600">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">18 mins</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Avg Clearance Time</div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-6">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-blue-500"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Built for Bengaluru. Powered by AI. Backed by Data.</span>
      </div>

      {/* Dashboard Widgets Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Live Overview */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Live Overview
            </h3>
            <span className="text-xs text-gray-500">Updated just now</span>
          </div>
          <div className="flex flex-col gap-4">
            {Object.entries(CAUSE_TOTALS).map(([cause, count], i) => {
              const label = cause.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
              const percentage = Math.round((count / totalCauses) * 100);
              const color = colors.causes[cause] || colors.causes.others;
              
              return (
                <div key={cause} className="flex items-center text-sm">
                  <div className="w-36 flex items-center gap-2">
                    <span className="w-4 h-4 rounded opacity-80" style={{backgroundColor: color}}></span>
                    <span className="text-gray-700 dark:text-gray-300 truncate">{label}</span>
                  </div>
                  <div className="flex-grow mx-4 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all duration-1000 ease-out"
                      style={{ 
                        width: mounted ? `${percentage}%` : '0%', 
                        backgroundColor: color,
                        transitionDelay: `${i * 100}ms`
                      }}
                    ></div>
                  </div>
                  <div className="w-12 text-right font-medium text-gray-900 dark:text-white">{count}</div>
                </div>
              );
            })}
          </div>
          <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700 text-center">
            <button onClick={() => setActiveView("hotspot")} className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors flex items-center justify-center gap-1 w-full">
              View All Causes <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
        </div>

        {/* Hotspot Map Preview */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm flex flex-col cursor-pointer hover:border-blue-300 transition-colors" onClick={() => setActiveView("hotspot")}>
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Hotspot Map</h3>
            <span className="text-xs font-medium text-blue-600 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded">View Full Map</span>
          </div>
          <div className="flex-grow bg-gray-100 dark:bg-gray-900 rounded-lg relative overflow-hidden flex items-center justify-center group pointer-events-none">
             <div ref={mapContainer} style={{ width: "100%", height: "100%" }}></div>
             <div className="absolute inset-0 bg-white/10 dark:bg-black/10"></div>
          </div>
        </div>

        {/* Live Events Feed */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Live Events</h3>
            <span onClick={() => setActiveView("hotspot")} className="text-xs font-medium text-blue-600 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/50">View All</span>
          </div>
          <div className="flex flex-col gap-0 overflow-y-auto pr-2" style={{ maxHeight: "250px" }}>
            {liveEvents.map((event, i) => (
              <div key={i} className="group flex items-start gap-3 py-3 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded transition-colors cursor-pointer" onClick={() => setActiveView("hotspot")}>
                <div className="mt-1 w-8 h-8 rounded-full flex items-center justify-center bg-opacity-10" style={{ backgroundColor: `${event.iconColor}20`, color: event.iconColor }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <div className="flex-grow min-w-0">
                  <div className="text-sm font-medium text-gray-900 dark:text-white truncate">{event.cause}</div>
                  <div className="text-xs text-gray-500 truncate">{event.location}</div>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className="text-[10px] text-gray-400">{event.time}</span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded" style={{ color: event.impactColor, backgroundColor: `${event.impactColor}15` }}>
                    {event.impact}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { id: "hotspot", title: "Hotspot Map", desc: "Explore incidents, hotspots and traffic density.", icon: "MapPinIcon", colorClass: "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400" },
          { id: "predict", title: "Predict Event", desc: "Predict clearance time, severity, and impact.", icon: "ZapIcon", colorClass: "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400" },
          { id: "classifier", title: "Classifier", desc: "Classify causes from multilingual reports.", icon: "MessageSquareIcon", colorClass: "bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400" },
          { id: "resolution", title: "Resolution Output", desc: "View AI-powered insights and predictions.", icon: "ClockIcon", colorClass: "bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400" },
          { id: "simulation", title: "Simulate", desc: "Simulate scenarios and evaluate impact.", icon: "ActivityIcon", colorClass: "bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400" }
        ].map((card) => (
          <div 
            key={card.id}
            onClick={() => setActiveView(card.id)}
            className="group bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 cursor-pointer hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md transition-all h-full flex flex-col relative overflow-hidden"
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${card.colorClass} group-hover:scale-110 transition-transform`}>
              {/* Simple generic icon based on the mapped type */}
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
            </div>
            <h4 className="font-semibold text-gray-900 dark:text-white mb-1 text-sm">{card.title}</h4>
            <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{card.desc}</p>
            <div className="mt-auto pt-3 flex justify-end">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-gray-300 dark:text-gray-600 group-hover:text-blue-500 transition-colors"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-16 text-center text-sm text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-800 pt-8">
        DRISHTI — Turning Data into Decisions. Anticipate. Act. Keep Bengaluru Moving.
      </div>
    </div>
  );
}

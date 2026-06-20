export const HOTSPOT_JUNCTIONS = [
  {
    name: "Silk Board Junction",
    lat: 12.9176,
    lng: 77.6244,
    count: 89,
    dominant_cause: "vehicle_breakdown",
  },
  {
    name: "KR Puram Bridge",
    lat: 13.004,
    lng: 77.6781,
    count: 81,
    dominant_cause: "accident",
  },
  {
    name: "Marathahalli Bridge",
    lat: 12.9592,
    lng: 77.6974,
    count: 76,
    dominant_cause: "water_logging",
  },
  {
    name: "Hebbal Flyover",
    lat: 13.0358,
    lng: 77.5978,
    count: 72,
    dominant_cause: "construction",
  },
  {
    name: "Tin Factory",
    lat: 13.0039,
    lng: 77.6749,
    count: 68,
    dominant_cause: "public_event",
  },
  {
    name: "Mekhri Circle",
    lat: 13.0076,
    lng: 77.5896,
    count: 60,
    dominant_cause: "others",
  },
  {
    name: "Yeshwanthpur",
    lat: 13.0238,
    lng: 77.5529,
    count: 55,
    dominant_cause: "vehicle_breakdown",
  },
  {
    name: "Sadashivanagar",
    lat: 13.0068,
    lng: 77.5713,
    count: 50,
    dominant_cause: "accident",
  },
  {
    name: "Sulthanpalya",
    lat: 13.0194,
    lng: 77.6047,
    count: 48,
    dominant_cause: "water_logging",
  },
  {
    name: "Nagavara",
    lat: 13.0416,
    lng: 77.6186,
    count: 45,
    dominant_cause: "construction",
  },
  {
    name: "Indiranagar",
    lat: 12.9719,
    lng: 77.6412,
    count: 42,
    dominant_cause: "public_event",
  },
  {
    name: "Koramangala",
    lat: 12.9352,
    lng: 77.6244,
    count: 40,
    dominant_cause: "others",
  },
  {
    name: "Bellandur",
    lat: 12.9279,
    lng: 77.6714,
    count: 38,
    dominant_cause: "vehicle_breakdown",
  },
  {
    name: "BTM Layout",
    lat: 12.9165,
    lng: 77.6101,
    count: 35,
    dominant_cause: "accident",
  },
  {
    name: "HSR Layout",
    lat: 12.91,
    lng: 77.645,
    count: 32,
    dominant_cause: "water_logging",
  },
  {
    name: "Doddakannalli",
    lat: 12.9135,
    lng: 77.6782,
    count: 30,
    dominant_cause: "construction",
  },
  {
    name: "JP Nagar",
    lat: 12.9063,
    lng: 77.5857,
    count: 28,
    dominant_cause: "public_event",
  },
  {
    name: "Jayanagar",
    lat: 12.9307,
    lng: 77.5832,
    count: 25,
    dominant_cause: "others",
  },
  {
    name: "Basaveshwaranagar",
    lat: 12.989,
    lng: 77.5385,
    count: 22,
    dominant_cause: "vehicle_breakdown",
  },
  {
    name: "Shivajinagar",
    lat: 12.9857,
    lng: 77.6058,
    count: 20,
    dominant_cause: "accident",
  },
  {
    name: "Frazer Town",
    lat: 12.9972,
    lng: 77.6133,
    count: 18,
    dominant_cause: "water_logging",
  },
  {
    name: "Vasanth Nagar",
    lat: 12.9896,
    lng: 77.5928,
    count: 15,
    dominant_cause: "construction",
  },
  {
    name: "Rajajinagar",
    lat: 12.988,
    lng: 77.5548,
    count: 12,
    dominant_cause: "public_event",
  },
  {
    name: "Banashankari",
    lat: 12.9254,
    lng: 77.5468,
    count: 10,
    dominant_cause: "others",
  },
  {
    name: "Herohalli",
    lat: 12.9978,
    lng: 77.4872,
    count: 8,
    dominant_cause: "vehicle_breakdown",
  },
];

export const CAUSE_TOTALS = {
  vehicle_breakdown: 312,
  accident: 241,
  water_logging: 156,
  construction: 188,
  public_event: 104,
  others: 93,
};

export const TOP_JUNCTIONS = [...HOTSPOT_JUNCTIONS]
  .sort((a, b) => b.count - a.count)
  .slice(0, 5);

export function mockPredictEvent() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        matched_event_id: "evt_4721",
        matched_description: "IPL opening ceremony · Cubbon Park",
        predicted_minutes: 240,
        confidence_band: "High",
        manpower_tier: "Tier 3",
        explanation:
          "Similar public events in CBD corridors required staged diversions and extended pedestrian clearance. The model weighs event scale, corridor capacity and prior deployment patterns.",
      });
    }, 800);
  });
}

export function mockClassify() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        event_cause: "vehicle_breakdown",
        confidence: 0.91,
      });
    }, 600);
  });
}

export const RESOLUTION_OUTPUT_MOCK = {
  predicted_minutes: 240,
  confidence_band: "High",
  manpower_tier: "Tier 3",
  explanation:
    "Similar public events in CBD corridors required staged diversions and extended pedestrian clearance. The model weighs event scale, corridor capacity and prior deployment patterns.",
  similar_events: [
    { name: "Marathon road closure", corridor: "CBD 1", duration: 228 },
    { name: "Stadium ingress event", corridor: "CBD 2", duration: 251 },
    { name: "Public gathering · MG Road", corridor: "CBD 1", duration: 236 },
  ],
  severity: { priority: "High", road_closure: false, event_type: "Unplanned" },
};

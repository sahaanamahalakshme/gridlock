# SENTRY (Gridlock)

SENTRY is an event-driven traffic forecasting and resource deployment system designed for Bengaluru. It leverages multiple machine learning models and a historical memory store to classify incoming traffic incidents (in Kannada, English, or code-mixed text), forecast their impact and resolution times, and provide precedent data to help deploy resources efficiently.

---

## Project Structure & Components

The application is modularized into the following core components:

### 1. `memory/` (The Database & Memory Store)
Stores live and historical events, providing precedent search capabilities.
- **`db.py` / `models.py` / `schema.sql`**: SQLAlchemy setup and database schema. Works on SQLite for local development and Postgres for production.
- **`memory_store.py`**: Handles writing new live events and retrieving similar historical events based on `police_station`, `event_cause`, and `corridor`.
- **`confidence.py`**: Calculates a confidence tier ("no_precedent", "thin", "moderate", "strong") based on the frequency of similar past events.

### 2. `ml_models/` (Machine Learning Models)
Contains three separate ML pipelines that can be independently trained and tested.
- **`bilingual_event_classifier/`**: 
  - *Goal*: Classifies raw event text (Kannada/English) into an `event_cause` and a `severity` priority.
  - *Under the hood*: Uses `sentence-transformers` to generate embeddings and Logistic Regression for the final classification.
- **`resolution_predictor/`**:
  - *Goal*: Predicts the number of minutes required to clear an incident based on structured features (cause, corridor, time of day, closure required, etc).
  - *Under the hood*: Employs an XGBoost regressor, trained on historical closure times.
- **`impact_forecaster/`**:
  - *Goal*: Retrieves similar historical events purely based on the text description to provide qualitative precedent.
  - *Under the hood*: Utilizes a Nearest Neighbors index over text embeddings.

### 3. Root Level Files
- **`app.py`**: The main FastAPI application. It orchestrates the memory store and the three ML models to provide endpoints for event reporting, classification, resolution tracking, and hotspot generation.
- **`pipeline.py`**: A standalone script that runs the full inference and data-logging pipeline.
- **`test_each_model.py` / `test_integration.py`**: Scripts to independently verify each ML model and test the end-to-end integration.

---

## How to Run the Application

### 1. Environment Setup

Ensure you have Python 3 installed. Install the dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Prepare the Database and Models

If this is your first time running the application, you need to set up the database and train/evaluate the models.

*Initialize the database and seed historical data (if applicable):*
```bash
python memory/seed_historical.py
```

*Train the ML Models (if they aren't pre-trained):*
Navigate to each model folder and run the respective scripts. For example, for the classifier:
```bash
python ml_models/bilingual_event_classifier/run_pipeline.py
```
*(Check the `src/` folders within each `ml_models` sub-directory for individual `clean_data.py`, `train_model.py`, etc., if you wish to run them separately.)*

### 3. Start the FastAPI Server

Run the backend server using `uvicorn`:

```bash
uvicorn app:app --reload
```

The server will start on `http://127.0.0.1:8000`.

### 4. Exploring the Endpoints

Once the server is running, you can access the interactive API documentation (Swagger UI) at:
**[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

Key Endpoints:
- `POST /classify`: Classify a raw text string into a cause and severity.
- `POST /events/report`: Log a new traffic event. This will automatically classify it, retrieve similar precedents, estimate resolution time, and store it.
- `PATCH /events/{event_id}/resolve`: Mark an event as resolved, which updates its duration and improves future predictions.
- `GET /events/hotspot`: Retrieve current traffic hotspot data.

---

## Testing

To verify that all machine learning models are functioning correctly:
```bash
python test_each_model.py
```

To run full integration tests:
```bash
python test_integration.py
```
# DRISHTI - Resolution Intelligence Dashboard

This is the DRISHTI Resolution Intelligence frontend application — an internal operational dashboard for Bengaluru traffic police, intended to interact with three ML models:
- Bilingual Event Classifier
- Impact Forecaster
- Resolution Predictor

Currently, this frontend is intentionally backend-independent until teammates' APIs are ready. It simulates backend calls utilizing predefined mock data to showcase and test UI functionality.

## How to Run

To run the application locally, install the dependencies and start the Vite development server:

```bash
npm install
npm run dev
```

The application will typically start at `http://localhost:5173`.

## Moving to Real API Data

Currently, all mock data and simulated endpoints are localized inside `src/mockData.js`. 

To transition from the UI mock state to the production application, edit **`src/mockData.js`** to swap out the mock functions for real `fetch()` calls once the teammate APIs are complete:

- Update `mockPredictEvent` to send `POST` requests with `formData` to the Impact Forecaster/Resolution Predictor endpoints.
- Update `mockClassify` to send the `text` string to the Bilingual Event Classifier API endpoint.
- Swap out `HOTSPOT_JUNCTIONS` and `CAUSE_TOTALS` to fetch live historical data instead of static arrays.

*Note: This architecture intentionally decouples the UI layout logic from data retrieval to maintain parallel development streams.*

# Two enhancements: confidence flag + civic routing

```
gridlock/
├── memory/
│   ├── confidence.py              ← UPDATE (add low_precedent + merge helper)
│   ├── seed_historical_FIXED.py   ← NEW (fixes a crash in your current seed script)
│   └── test_confidence_flag.py    ← NEW (verifies the 248/509 number)
└── ml_models/
    └── bilingual_event_classifier/
        ├── routing_map.py              ← NEW
        └── test_routing_classifier.py  ← NEW (verifies the 1,645 number)
```

## 1. Confidence flag (memory/)

**What changed:** `confidence.py` now returns a `low_precedent` boolean
(`count < 5`) alongside the existing 4-tier system, plus a new
`enrich_with_confidence()` helper that stamps that same confidence block
onto any list of match dicts — specifically so it can tag the Impact
Forecaster's semantic matches, which is the one place the original idea
wanted it that wasn't already covered.

## Run order

python reset_db.py
python seed_historical.py
python patch_seed_planned.py
python test_confidence_flag.py        # should print 248/509, 48.7%

# 2. verify routing independently of the DB (works on the raw CSV directly)
cd ../ml_models/bilingual_event_classifier
python testing_route_classifier.py     # should print civic count = 1645

```
SENTRY — Temporal Baseline & Repeat Hotspot Flag

Two analytical enhancements to the existing Gridlock pipeline


What these features do — and why they matter to judges

Feature 1: Temporal Baseline — "Is this a spike or just business as usual?"

The problem it solves: When a new event comes in at 21:00 on Mysore Road, SENTRY
currently has no way to say whether that's unusual. Our data shows 21:00 is peak hour
with 810 events/hr system-wide — so a new Mysore Road event at 21:00 is completely
normal. A new event at 12:00 is extraordinary. Without a baseline, every event looks
the same. With a baseline, SENTRY can say: "This is 6.4× the normal rate — treat as
spike" vs "This is within normal range — routine dispatch."

How it works:


Pre-compute: average events per corridor per hour-of-day from all 152 days of data
At runtime: when a new event arrives, compare current hourly rate on that corridor
to the historical baseline
Output: spike_ratio (e.g. 6.4×), spike_label (normal / elevated / spike / severe),
is_spike boolean, plus a human-readable explanation string


Data source: All 8,173 ASTRAM records. Pure pandas — no ML model needed.
Build time: ~2 hours.


Feature 2: Repeat Hotspot Flag — "Chronic location vs one-off incident"

The problem it solves: 138 addresses have 10+ historical events. The #1 hotspot
(Marathahalli ORR) has 88 events. When a new breakdown comes in at that exact location,
an officer should know immediately: "This is a known chronic problem location, not a
random incident." This changes their response — chronic hotspots may need infrastructure
fixes (BBMP escalation), not just traffic dispatch. One-off incidents need immediate
response but no long-term flag.

How it works:


Pre-compute: index all junctions (85 with 10+ events) and addresses (138 with 10+)
into a lookup dictionary
At runtime: when a new event arrives, fuzzy-match its address/junction against the
hotspot index
Output: is_hotspot boolean, hotspot_tier (critical/high/moderate), historical_count,
dominant_cause, avg_resolution_min, plus a route_to suggestion (Traffic Police,
BBMP, or BWSSB) based on cause mix


Data source: All 8,173 ASTRAM records. Pure pandas + rapidfuzz for address matching.
Build time: ~1 hour.


Where these plug into your existing codebase

gridlock/
├── app.py                          ← ADD: import and call both enhancements in POST /events/report
├── memory/
│   └── memory_store.py             ← ADD: write spike_ratio + hotspot fields to DB on each event
├── ml_models/
│   ├── bilingual_event_classifier/
│   ├── impact_forecaster/
│   ├── resolution_predictor/
│   ├── temporal_baseline/          ← NEW (this feature)
│   │   ├── README.md
│   │   ├── data/
│   │   │   └── astram_raw.csv      ← symlink or copy your main CSV here
│   │   ├── src/
│   │   │   ├── build_baseline.py   ← STEP 1: run once, generates baseline JSON
│   │   │   └── score.py            ← STEP 2: called at inference time by app.py
│   │   └── output/
│   │       └── baseline.json       ← generated artefact
│   └── hotspot_flag/               ← NEW (this feature)
│       ├── README.md
│       ├── data/
│       │   └── astram_raw.csv
│       ├── src/
│       │   ├── build_index.py      ← STEP 1: run once, generates hotspot index JSON
│       │   └── flag.py             ← STEP 2: called at inference time by app.py
│       └── output/
│           └── hotspot_index.json  ← generated artefact
└── frontend/
    └── src/
        └── mockData.js             ← ADD: spike_ratio + hotspot fields to mock response shape


Order of execution

One-time setup (run before starting the server)

bash# 1. Build the temporal baseline lookup table
cd gridlock/ml_models/temporal_baseline
python src/build_baseline.py
# → Writes output/baseline.json (~22KB, one row per corridor×hour combination)

# 2. Build the hotspot index
cd gridlock/ml_models/hotspot_flag
python src/build_index.py
# → Writes output/hotspot_index.json (~45KB, junction + address lookups)

Runtime (called automatically by app.py on every POST /events/report)

pythonfrom ml_models.temporal_baseline.src.score import load_baseline, score_spike
from ml_models.hotspot_flag.src.flag import load_hotspot_index, flag_hotspot

# Load once at server startup
baseline = load_baseline()
hotspot_index = load_hotspot_index()

# Call per request
spike_result   = score_spike(baseline, corridor="Mysore Road", current_hour=21, live_count=3)
hotspot_result = flag_hotspot(hotspot_index, junction="MekhriCircle", address="...")

Verification

bash# Smoke-test both modules end to end
python src/build_baseline.py      # should print summary table
python src/score.py               # runs 5 demo cases
python src/build_index.py         # should print top hotspots
python src/flag.py                # runs 3 demo cases


Input / Output contracts (exact shapes)

Temporal Baseline

Input to score_spike():

python{
    "corridor": "Mysore Road",          # str — from the incoming event
    "current_hour": 21,                 # int 0–23 — datetime.now().hour
    "live_count": 3,                    # int — events on this corridor in the last 60 min
                                        #        (query your DB: SELECT COUNT(*) WHERE ...)
}

Output from score_spike():

python{
    "spike_ratio": 6.42,                # float — live_count / avg_per_day_at_this_hour
    "spike_label": "spike",             # str: "normal" | "elevated" | "spike" | "severe"
    "is_spike": True,                   # bool — True if spike_ratio >= 3.0
    "baseline_avg": 0.467,             # float — historical avg events/day at this hour
    "hour": 21,
    "corridor": "Mysore Road",
    "explanation": "Mysore Road at 21:00 is running 6.4× above the historical baseline "
                   "(0.47 avg events/hr). This qualifies as a spike. Peak hours on this "
                   "corridor are 19:00–22:00 — treat as elevated-priority dispatch.",
}

Hotspot Flag

Input to flag_hotspot():

python{
    "junction": "MekhriCircle",         # str | None — from the incoming event
    "address": "Sankey Road, ...",      # str | None — raw address string
}

Output from flag_hotspot():

python{
    "is_hotspot": True,
    "hotspot_tier": "high",             # str: "critical" (50+) | "high" (25–49) | "moderate" (10–24) | None
    "historical_count": 64,             # int — total events at this location
    "dominant_cause": "vehicle_breakdown",
    "cause_breakdown": {                # top 3 causes with counts
        "vehicle_breakdown": 48,
        "pot_holes": 9,
        "water_logging": 7,
    },
    "avg_resolution_min": 54.1,         # float | None
    "route_to": "Traffic Police",       # str: "Traffic Police" | "BBMP" | "BWSSB"
    "route_reason": "vehicle_breakdown is the dominant cause (75% of events). "
                    "Standard traffic dispatch applies.",
    "match_type": "junction",           # str: "junction" | "address_exact" | "address_fuzzy" | "none"
    "match_score": 100,                 # int 0–100 — fuzzy match confidence
}

Combined response shape in app.py POST /events/report

These two dicts merge into the existing response as a context block:

python{
    "event_id": "...",
    "classification": {...},            # existing
    "resolution_prediction": {...},     # existing
    "similar_events": [...],            # existing
    "context": {                        # NEW
        "temporal": spike_result,
        "hotspot":  hotspot_result,
    }
}

The frontend reads response.context.temporal.spike_label and
response.context.hotspot.is_hotspot to decide how to render the event card.


What the frontend shows

Temporal baseline:


A subtle banner above the resolution card: "⚠ Spike detected — 6.4× above baseline
for Mysore Road at 21:00" (amber background if spike, red if severe, nothing if normal)
Small inline text on the map marker: "6.4×" badge


Hotspot flag:


Map marker gets a distinct outline ring if is_hotspot: true
Junction detail drawer shows: "Known chronic hotspot · 64 historical events · BBMP
escalation suggested" section
Route-to badge: colored pill saying "Traffic Police" / "BBMP" / "BWSSB"



Why these are worth building (for the pitch)

Both features are:


Honest: They're pure statistics on real data — nothing invented
Explainable: Every output has an explanation string that traces back to specific
counts from the CSV — judges can verify any number
Cheap to build: No GPU, no new model, no extra data needed
High visual impact: spike ratio and hotspot tier appear on every event card and
every map marker — they're visible in every demo moment
Non-obvious: Most traffic management systems don't distinguish "spike vs baseline"
or "chronic vs one-off" — this is the kind of insight that only comes from having
real historical data, which is exactly what ASTRAM gives you

# SENTRY / DRISHTI — Integration Guide
## Temporal Baseline + Repeat Hotspot Flag into existing backend and frontend

**Status of these two models:** Already trained and producing correct output.  
**Goal of this document:** Wire them into `app.py` (backend) and the three frontend
screens that should surface their output — no new screen required.

---

## Table of Contents

1. [What the two models return](#1-what-the-two-models-return)
2. [Backend changes — app.py](#2-backend-changes--apppy)
3. [Backend changes — memory/models.py (optional persistence)](#3-backend-changes--memorymodelspy)
4. [Frontend changes — Screen by screen](#4-frontend-changes--screen-by-screen)
   - [HotspotMap.jsx](#41-hotspotmapjsx)
   - [PredictEvent.jsx](#42-predicteventjsx)
   - [ResolutionOutput.jsx](#43-resolutionoutputjsx)
   - [Classifier.jsx — no change needed](#44-classifierjsx--no-change-needed)
   - [Simulate.jsx — no change needed](#45-simulatejsx--no-change-needed)
5. [Exact API response shape the frontend reads](#5-exact-api-response-shape-the-frontend-reads)
6. [Conditional rendering rules](#6-conditional-rendering-rules)
7. [Run order](#7-run-order)

---

## 1. What the two models return

These are the exact output shapes your backend already produces.
**Do not change these shapes** — the frontend changes below read from them directly.

### Temporal Baseline — `score_spike()` output
```json
{
  "spike_ratio": 6.42,
  "spike_label": "spike",
  "is_spike": true,
  "baseline_avg": 0.4671,
  "effective_rate": 3.0,
  "hour": 21,
  "corridor": "Mysore Road",
  "is_peak_hour": true,
  "data_source": "corridor_specific",
  "explanation": "Mysore Road at 21:00 is running 6.4× above the historical baseline..."
}
```

### Hotspot Flag — `flag_hotspot()` output
```json
{
  "is_hotspot": true,
  "hotspot_tier": "critical",
  "historical_count": 64,
  "dominant_cause": "vehicle_breakdown",
  "cause_breakdown": {
    "vehicle_breakdown": 55,
    "others": 5,
    "road_conditions": 3
  },
  "avg_resolution_min": 78.2,
  "route_to": "Traffic Police",
  "route_reason": "vehicle_breakdown is dominant (86%). Standard dispatch.",
  "match_type": "junction",
  "match_score": 100,
  "matched_name": "MekhriCircle"
}
```

---

## 2. Backend changes — app.py

### 2a. Add imports (top of file, with your existing imports)

```python
# ADD these two lines alongside your existing model imports
from ml_models.temporal_baseline.src.score import load_baseline, score_spike
from ml_models.hotspot_flag.src.flag import load_hotspot_index, flag_hotspot
from datetime import datetime, timezone, timedelta
```

### 2b. Load at startup (inside your existing startup block)

Your current startup event loads the classifier, resolution predictor, and impact
forecaster. Add two more lines in the same block:

```python
@app.on_event("startup")
async def startup():
    # --- your existing lines stay exactly as they are ---
    app.state.classifier  = load_classifier()
    app.state.predictor   = load_predictor()
    app.state.forecaster  = load_forecaster()

    # ADD these two lines
    app.state.baseline       = load_baseline()
    app.state.hotspot_index  = load_hotspot_index()
```

### 2c. Call inside POST /events/report

Find your existing `/events/report` endpoint. After classification runs and before
you build the return dict, add the following block.

```python
@app.post("/events/report")
async def report_event(payload: EventPayload, db: Session = Depends(get_session), request: Request = None):

    # ── [EXISTING] classify, predict, retrieve ────────────────────────────────
    classification     = classify(payload.description, request.app.state.classifier)
    resolution         = predict_resolution(payload, request.app.state.predictor)
    similar_events     = retrieve_similar_event(payload.description, request.app.state.forecaster)

    # ── [ADD] Temporal Baseline ───────────────────────────────────────────────
    # Count live events on this corridor in the last 60 minutes
    # (query your existing Event table — change column names if yours differ)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    live_count = (
        db.query(Event)
        .filter(
            Event.corridor == (payload.corridor or "Non-corridor"),
            Event.start_datetime >= one_hour_ago,
        )
        .count()
    )

    spike_result = score_spike(
        request.app.state.baseline,
        corridor=payload.corridor or "Non-corridor",
        current_hour=datetime.now(timezone.utc).hour,
        live_count=live_count,
    )

    # ── [ADD] Hotspot Flag ────────────────────────────────────────────────────
    hotspot_result = flag_hotspot(
        request.app.state.hotspot_index,
        junction=getattr(payload, "junction", None),   # pass None if your payload
        address=getattr(payload, "address", None),      # doesn't have these fields yet
    )

    # ── [ADD] Merge into response — add a "context" key to your existing return ──
    return {
        # --- your existing keys stay exactly as they are ---
        "event_id":              new_event.id,
        "classification":        classification,
        "resolution_prediction": resolution,
        "similar_events":        similar_events,
        "confidence":            confidence_result,   # your existing confidence module

        # ADD this key
        "context": {
            "temporal": spike_result,
            "hotspot":  hotspot_result,
        },
    }
```

### 2d. If your EventPayload doesn't have junction/address fields yet

Add them as optional fields in your Pydantic model — the hotspot flag handles None
gracefully, so this won't break anything if they're absent:

```python
# In your Pydantic EventPayload model (wherever it's defined)
class EventPayload(BaseModel):
    # --- your existing fields ---
    description: str
    corridor: Optional[str] = None
    police_station: Optional[str] = None
    event_cause: Optional[str] = None
    requires_road_closure: bool = False

    # ADD these (both optional — flag() handles None)
    junction: Optional[str] = None
    address: Optional[str] = None
```

### 2e. Also expose from GET /events/hotspot

Your hotspot map screen calls `GET /events/hotspot` to get active events.
Add `hotspot_tier` to each item in that response so the map can render the
chronic-location ring without a separate call:

```python
@app.get("/events/hotspot")
async def get_hotspots(request: Request, db: Session = Depends(get_session)):
    events = db.query(Event).filter(Event.status == "active").all()

    result = []
    for e in events:
        # [ADD] flag each event on the way out
        hf = flag_hotspot(
            request.app.state.hotspot_index,
            junction=e.junction,
            address=e.address,
        )
        result.append({
            # your existing fields
            "event_id":    e.id,
            "junction":    e.junction,
            "lat":         e.latitude,
            "lng":         e.longitude,
            "event_cause": e.event_cause,
            "count":       e.count,           # however you aggregate this

            # ADD
            "is_hotspot":    hf["is_hotspot"],
            "hotspot_tier":  hf["hotspot_tier"],
            "historical_count": hf["historical_count"],
            "route_to":      hf["route_to"],
        })

    return result
```

---

## 3. Backend changes — memory/models.py (optional but recommended)

Persist the two context fields so they're queryable for analytics and future
retraining. Add to your existing `Event` SQLAlchemy model:

```python
class Event(Base):
    # --- your existing columns ---
    id              = Column(String, primary_key=True)
    description     = Column(String)
    corridor        = Column(String)
    event_cause     = Column(String)
    start_datetime  = Column(DateTime)
    # ... etc

    # ADD these 5 columns
    spike_ratio     = Column(Float,   nullable=True)
    spike_label     = Column(String,  nullable=True)   # "normal"|"elevated"|"spike"|"severe"
    is_hotspot      = Column(Boolean, nullable=True)
    hotspot_tier    = Column(String,  nullable=True)   # "critical"|"high"|"moderate"|null
    route_to        = Column(String,  nullable=True)   # "Traffic Police"|"BBMP"|"BWSSB"
```

Then in `memory_store.py` `write_event()`, set them before commit:

```python
def write_event(session, event_data: dict, spike_result: dict, hotspot_result: dict):
    new_event = Event(
        # --- your existing assignments ---
        **event_data,

        # ADD
        spike_ratio  = spike_result.get("spike_ratio"),
        spike_label  = spike_result.get("spike_label"),
        is_hotspot   = hotspot_result.get("is_hotspot"),
        hotspot_tier = hotspot_result.get("hotspot_tier"),
        route_to     = hotspot_result.get("route_to"),
    )
    session.add(new_event)
    session.commit()
```

---

## 4. Frontend changes — Screen by screen

The `context` key now arrives on every `/events/report` response.
Here is exactly what to add to each screen file.

---

### 4.1 HotspotMap.jsx

**Goal:** Show a dashed outline ring on chronic hotspot markers.
Add a "Chronic locations" stat to the right panel.

**Where the data comes from:** `GET /events/hotspot` — each item now includes
`is_hotspot`, `hotspot_tier`, `historical_count` (added in step 2e above).

#### Change 1 — Marker rendering (inside your existing marker loop)

Find where you currently call `L.circleMarker(...)` or equivalent.
Add a second layer marker for chronic locations:

```jsx
// EXISTING — your cause-colored circle marker (keep this exactly)
L.circleMarker([event.lat, event.lng], {
  radius: computeRadius(event.count),
  fillColor: CAUSE_COLORS[event.event_cause] || "#6B7280",
  color: "#0b0e0a",
  weight: 1,
  fillOpacity: 0.85,
}).addTo(map).bindPopup(...);

// ADD — chronic hotspot ring (only renders when is_hotspot is true)
if (event.is_hotspot) {
  L.circleMarker([event.lat, event.lng], {
    radius: computeRadius(event.count) + 5,   // slightly larger than the fill marker
    fillColor: "transparent",
    color: event.hotspot_tier === "critical" ? "#DC2626" : "#D97706",
    weight: 2,
    dashArray: "4 3",                           // dashed outline
    fillOpacity: 0,
    interactive: false,                         // ring is visual-only, not clickable
  }).addTo(map);
}
```

#### Change 2 — Right panel stats block

Find your existing stats panel (where you show "Total junctions: 25", "Peak junction").
Add one more stat:

```jsx
{/* EXISTING stats — keep these */}
<div className="stat-block">
  <p className="stat-label">TOTAL JUNCTIONS</p>
  <p className="stat-value">{stats.totalJunctions}</p>
</div>
<div className="stat-block">
  <p className="stat-label">PEAK JUNCTION</p>
  <p className="stat-value">{stats.peakJunction}</p>
</div>

{/* ADD this stat */}
<div className="stat-block">
  <p className="stat-label">CHRONIC LOCATIONS</p>
  <p className="stat-value" style={{ color: "#DC2626" }}>
    {events.filter(e => e.is_hotspot).length}
  </p>
  <p className="stat-sub">10+ historical events</p>
</div>
```

#### Change 3 — Junction detail drawer (if you've built this)

Inside the drawer that opens on marker click, add a hotspot section
before the cause breakdown:

```jsx
{/* ADD — only renders when is_hotspot is true */}
{selectedEvent.is_hotspot && (
  <div className="drawer-hotspot-banner">
    <span className={`tier-badge tier-${selectedEvent.hotspot_tier}`}>
      {selectedEvent.hotspot_tier?.toUpperCase()} HOTSPOT
    </span>
    <p className="drawer-hotspot-text">
      {selectedEvent.historical_count} historical events at this location.
    </p>
    <p className="drawer-route-to">
      Route to: <strong>{selectedEvent.route_to}</strong>
    </p>
  </div>
)}
```

---

### 4.2 PredictEvent.jsx

**Goal:** Show two conditional pills in the result card:
`[2.1× SPIKE]` and `[CHRONIC LOCATION]`.
Show civic routing recommendation when `route_to !== "Traffic Police"`.

**Where the data comes from:** `response.context.temporal` and `response.context.hotspot`
from the `POST /events/report` response.

#### Change 1 — Store context in component state

```jsx
// EXISTING state (keep these)
const [result, setResult] = useState(null);
const [loading, setLoading] = useState(false);

// ADD
const [context, setContext] = useState(null);

// EXISTING — in your submit handler, after getting the response
const handleSubmit = async () => {
  setLoading(true);
  const response = await fetch("/events/report", { method: "POST", ... });
  const data = await response.json();

  setResult(data);         // existing
  setContext(data.context); // ADD this line — that's the only change to the handler
  setLoading(false);
};
```

#### Change 2 — Context pill row in result card

Add this block **directly after your existing badge row** (the row with FKID001700,
LOW PRECEDENT, CONFIDENCE: THIN):

```jsx
{/* ADD — context pill row, renders only when data is present */}
{context && (
  <div className="context-pill-row">

    {/* Spike pill — only shows when is_spike is true */}
    {context.temporal?.is_spike && (
      <span className={`context-pill pill-${context.temporal.spike_label}`}>
        {context.temporal.spike_ratio.toFixed(1)}× {context.temporal.spike_label.toUpperCase()}
        <span className="pill-sub"> · {context.temporal.corridor} {context.temporal.hour}:00</span>
      </span>
    )}

    {/* Hotspot pill — only shows when is_hotspot is true */}
    {context.hotspot?.is_hotspot && (
      <span className={`context-pill pill-hotspot pill-${context.hotspot.hotspot_tier}`}>
        CHRONIC LOCATION · {context.hotspot.historical_count} prior events
      </span>
    )}

  </div>
)}
```

#### Change 3 — Civic routing banner (BBMP / BWSSB)

Add this block **below the manpower recommendation** in your result card.
This is the most operationally useful output from the hotspot flag:

```jsx
{/* ADD — civic routing banner, only shows when route is not Traffic Police */}
{context?.hotspot?.route_to && context.hotspot.route_to !== "Traffic Police" && (
  <div className="civic-routing-banner">
    <span className="routing-dept">{context.hotspot.route_to}</span>
    <p className="routing-reason">{context.hotspot.route_reason}</p>
  </div>
)}
```

#### CSS to add (in your existing stylesheet or inline)

```css
/* Context pill row */
.context-pill-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 8px 0 12px;
}

.context-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.04em;
}

/* Spike severity colors */
.pill-elevated  { background: #FAEEDA; color: #92400E; border: 1px solid #D97706; }
.pill-spike     { background: #FEF3C7; color: #B45309; border: 1px solid #F59E0B; }
.pill-severe    { background: #FEE2E2; color: #991B1B; border: 1px solid #DC2626; }

/* Hotspot tier colors */
.pill-hotspot.pill-moderate { background: #FEF3C7; color: #B45309; border: 1px solid #D97706; }
.pill-hotspot.pill-high     { background: #FEE2E2; color: #991B1B; border: 1px solid #DC2626; }
.pill-hotspot.pill-critical { background: #DC2626; color: #ffffff; border: 1px solid #B91C1C; }

.pill-sub { font-weight: 400; opacity: 0.75; }

/* Civic routing banner */
.civic-routing-banner {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-left: 3px solid #2563EB;
  border-radius: 4px;
  padding: 10px 14px;
  margin-top: 12px;
}
.routing-dept   { font-weight: 600; font-size: 12px; color: #1D4ED8; text-transform: uppercase; }
.routing-reason { font-size: 13px; color: #374151; margin-top: 3px; line-height: 1.5; }
```

---

### 4.3 ResolutionOutput.jsx

**Goal:** Add a 4th metric card "TRAFFIC CONTEXT" alongside the existing three
(Predicted Clearance, Confidence Band, Manpower Tier).

**Where the data comes from:** This screen receives the full prediction response.
If you're passing props down from PredictEvent.jsx, pass `context` as a prop.
If ResolutionOutput.jsx fetches independently, the same `response.context` key
is available in the API response.

#### Change 1 — Accept context as prop

```jsx
// EXISTING
function ResolutionOutput({ predicted_minutes, confidence_band, manpower_tier, explanation }) {

// CHANGE TO
function ResolutionOutput({ predicted_minutes, confidence_band, manpower_tier, explanation, context }) {
```

#### Change 2 — Add 4th metric card

Find where your three metric cards are rendered. Add a 4th immediately after the
Manpower Tier card:

```jsx
{/* EXISTING — your three cards, keep these */}
<MetricCard label="PREDICTED CLEARANCE" value={`${predicted_minutes} min`} />
<MetricCard label="CONFIDENCE BAND"     value={confidenceBandLabel} />
<MetricCard label="MANPOWER TIER"       value={manpower_tier} />

{/* ADD — 4th card, only renders when context exists */}
{context?.temporal && (
  <div className="metric-card traffic-context-card">
    <p className="metric-label">TRAFFIC CONTEXT</p>
    <p className={`metric-value spike-${context.temporal.spike_label}`}>
      {context.temporal.is_spike
        ? `${context.temporal.spike_ratio.toFixed(1)}× normal`
        : "Normal traffic"}
    </p>
    <p className="metric-sub">
      {context.temporal.corridor} · {String(context.temporal.hour).padStart(2,"0")}:00
      {context.temporal.is_peak_hour ? " · Peak hour" : ""}
    </p>
  </div>
)}
```

#### Change 3 — Hotspot context below explanation

Below your existing explanation box, add:

```jsx
{/* ADD — hotspot note, only renders when is_hotspot is true */}
{context?.hotspot?.is_hotspot && (
  <div className="hotspot-context-box">
    <p className="hotspot-context-label">CHRONIC LOCATION</p>
    <p className="hotspot-context-text">
      {context.hotspot.historical_count} prior incidents at this location.
      Dominant cause: {context.hotspot.dominant_cause?.replace(/_/g, " ")}{" "}
      ({Math.round(
        (context.hotspot.cause_breakdown?.[context.hotspot.dominant_cause] /
          context.hotspot.historical_count) * 100
      )}% of events).
      {context.hotspot.avg_resolution_min
        ? ` Avg clearance: ${context.hotspot.avg_resolution_min} min.`
        : ""}
    </p>
  </div>
)}
```

#### CSS to add

```css
/* 4th metric card — traffic context */
.traffic-context-card { border-top: 2px solid #E5E7EB; }
.spike-normal   .metric-value { color: #15803D; }
.spike-elevated .metric-value { color: #B45309; }
.spike-spike    .metric-value { color: #B45309; }
.spike-severe   .metric-value { color: #DC2626; }

/* Hotspot context box */
.hotspot-context-box {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-left: 3px solid #DC2626;
  border-radius: 4px;
  padding: 12px 16px;
  margin-top: 16px;
}
.hotspot-context-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #DC2626;
  margin-bottom: 4px;
}
.hotspot-context-text {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
}
```

---

### 4.4 Classifier.jsx — no change needed

The classifier screen's single purpose is showing the bilingual classification result
(event_cause + confidence). Mixing in hotspot or spike context here would dilute that
demo moment. The classifier POST `/classify` endpoint also doesn't receive junction or
corridor info, so there's nothing to match against anyway. Leave this screen as-is.

---

### 4.5 Simulate.jsx — no change needed

The simulation screen shows staged resolution progression. Temporal baseline and hotspot
data are event-level enrichment — they don't change the simulation stages or timing.
Leave this screen as-is.

---

## 5. Exact API response shape the frontend reads

This is the complete new shape of `POST /events/report`. The frontend reads from
`response.context.temporal` and `response.context.hotspot` only.
Everything else is unchanged from your current implementation.

```json
{
  "event_id": "evt_001",

  "classification": {
    "event_cause": "vehicle_breakdown",
    "confidence": 0.91,
    "route_to": "Traffic Police"
  },

  "resolution_prediction": {
    "predicted_minutes": 54,
    "confidence_band": [24, 84],
    "manpower_tier": "Tier 2 — 2 units",
    "explanation": "..."
  },

  "similar_events": [...],

  "confidence": {
    "tier": "moderate",
    "similar_count": 47
  },

  "context": {
    "temporal": {
      "spike_ratio": 6.42,
      "spike_label": "spike",
      "is_spike": true,
      "baseline_avg": 0.4671,
      "effective_rate": 3.0,
      "hour": 21,
      "corridor": "Mysore Road",
      "is_peak_hour": true,
      "explanation": "Mysore Road at 21:00 is running 6.4× above the historical baseline..."
    },
    "hotspot": {
      "is_hotspot": true,
      "hotspot_tier": "critical",
      "historical_count": 64,
      "dominant_cause": "vehicle_breakdown",
      "cause_breakdown": { "vehicle_breakdown": 55, "others": 5, "road_conditions": 3 },
      "avg_resolution_min": 78.2,
      "route_to": "Traffic Police",
      "route_reason": "vehicle_breakdown is dominant (86%). Standard dispatch.",
      "match_type": "junction",
      "match_score": 100,
      "matched_name": "MekhriCircle"
    }
  }
}
```

---

## 6. Conditional rendering rules

Apply these exactly — they keep the UI quiet when nothing is wrong and loud
only when something needs attention:

| Condition | What renders |
|---|---|
| `is_spike: false` | Nothing. No "NORMAL" badge. Silence is the signal. |
| `is_spike: true, spike_label: "elevated"` | Amber pill: `1.8× ELEVATED` |
| `is_spike: true, spike_label: "spike"` | Amber/orange pill: `6.4× SPIKE` |
| `is_spike: true, spike_label: "severe"` | Red pill: `12×+ SEVERE` |
| `is_hotspot: false` | Nothing. No badge. No ring on the map marker. |
| `is_hotspot: true, tier: "moderate"` | Amber dashed ring + amber pill |
| `is_hotspot: true, tier: "high"` | Red dashed ring + red pill |
| `is_hotspot: true, tier: "critical"` | Red filled ring + red pill |
| `route_to: "Traffic Police"` | No routing banner. This is the default. |
| `route_to: "BBMP"` | Blue routing banner with reason text |
| `route_to: "BWSSB"` | Blue routing banner with reason text |

---

## 7. Run order

### Before starting the server (one-time setup, already done if you trained the models)

```bash
# Only needed if output JSON files don't exist yet
cd gridlock/ml_models/temporal_baseline
python src/build_baseline.py
# → creates output/baseline.json

cd gridlock/ml_models/hotspot_flag
python src/build_index.py
# → creates output/hotspot_index.json
```

### Starting the server (no change to your existing command)

```bash
uvicorn app:app --reload
# load_baseline() and load_hotspot_index() now run at startup
# Both load in under 1 second — no startup delay
```

### Verifying the integration works

```bash
# Hit the endpoint and check the context key is present
curl -X POST http://localhost:8000/events/report \
  -H "Content-Type: application/json" \
  -d '{
    "description": "BMTC bus breakdown near Bellandur gate",
    "corridor": "ORR East 1",
    "police_station": "Bellandur",
    "junction": "SilkBoardJunc",
    "requires_road_closure": false
  }'

# Expected: response JSON includes "context": { "temporal": {...}, "hotspot": {...} }
# If context key is missing, check that load_baseline() and load_hotspot_index()
# are being called in your startup block and stored on app.state
```

### Verifying the frontend picks up the data

Open PredictEvent, submit any form. Open browser DevTools → Network tab →
find the `/events/report` request → check Response JSON for the `context` key.
If `context.temporal.is_spike` is `true`, you should see the amber spike pill
appear in the result card immediately.

---

## Summary of all files touched

| File | Change type | Lines changed |
|---|---|---|
| `app.py` | Add 2 imports, 2 startup lines, ~20 lines in endpoint | ~25 lines |
| `memory/models.py` | Add 5 optional columns | 5 lines |
| `memory/memory_store.py` | Set 5 new fields in write_event() | 5 lines |
| `frontend/src/screens/HotspotMap.jsx` | Chronic ring + 1 stat + drawer section | ~30 lines |
| `frontend/src/screens/PredictEvent.jsx` | context state + 2 conditional blocks | ~40 lines |
| `frontend/src/screens/ResolutionOutput.jsx` | 4th metric card + hotspot note | ~25 lines |
| `frontend/src/screens/Classifier.jsx` | **No change** | 0 lines |
| `frontend/src/screens/Simulate.jsx` | **No change** | 0 lines |

Total new code across the entire project: approximately **130 lines**.
No new screens. No new dependencies. No changes to your trained model files.

"""FastAPI entry point orchestrating ML models and memory store."""

from fastapi import FastAPI, Depends, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from sqlalchemy import func, text

from datetime import datetime, timezone

from typing import Optional

from memory.db import get_session, init_db

from memory.memory_store import read_similar_events, write_event

from memory.models import Event

from serialization import clean_numpy

from ml_models.bilingual_event_classifier.predict import classify

from ml_models.resolution_predictor.src.predict import (
    load_artifacts as load_resolution,
    predict as predict_resolution,
)

from ml_models.impact_forecaster.src.retrieve import retrieve_similar_event

app = FastAPI(
    title="SENTRY",
    description="Event-driven traffic forecasting and resource deployment for Bengaluru",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_resolution_artifacts = None


@app.on_event("startup")
def startup():

    global _resolution_artifacts

    init_db()

    _resolution_artifacts = load_resolution()

    print("[startup] All artifacts loaded.")


class ClassifyRequest(BaseModel):

    description: str = Field(..., example="ಬಿಎಂಟಿಸಿ ಬಸ್ ಕೆಟ್ಟು ನಿಂತಿದೆ ಸರ್")


class ReportEventRequest(BaseModel):

    description: str

    corridor: Optional[str] = None

    police_station: str

    latitude: float

    longitude: float

    requires_road_closure: bool = False

    event_type: Optional[str] = "unplanned"

    zone: Optional[str] = None

    junction: Optional[str] = None

    address: Optional[str] = None


class ResolveEventRequest(BaseModel):

    closed_datetime: Optional[datetime] = None


@app.get("/")
def root():

    return {"message": "Welcome to SENTRY. Visit /docs for interactive documentation."}


@app.get("/health")
def health():

    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/classify")
def classify_endpoint(body: ClassifyRequest):

    return classify(body.description)


@app.post("/events/report")
def report_event(body: ReportEventRequest, session: Session = Depends(get_session)):

    classification = classify(body.description)

    event_cause = classification["event_cause"]

    severity = classification["severity"]

    precedent = read_similar_events(
        session,
        police_station=body.police_station,
        event_cause=event_cause,
        corridor=body.corridor,
    )

    matches_with_duration = [
        m for m in precedent["matches"] if m.get("duration_minutes") is not None
    ]

    raw_text_matches = retrieve_similar_event(
        event_cause=event_cause,
        corridor=body.corridor or "Non-corridor",
        description=body.description,
        k=3,
    )

    text_matches = clean_numpy(raw_text_matches)

    resolution = predict_resolution(
        _resolution_artifacts,
        {
            "event_cause": event_cause,
            "corridor": body.corridor or "Non-corridor",
            "priority": severity if severity in ("High", "Low") else "Low",
            "requires_road_closure": body.requires_road_closure,
            "police_station": body.police_station,
        },
    )

    written = write_event(
        session,
        {
            "event_type": body.event_type or "unplanned",
            "event_cause": event_cause,
            "status": "active",
            "police_station": body.police_station,
            "corridor": body.corridor,
            "zone": body.zone,
            "junction": body.junction,
            "address": body.address,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "priority": severity if severity in ("High", "Low") else None,
            "requires_road_closure": body.requires_road_closure,
            "description": body.description,
            "start_datetime": datetime.now(timezone.utc),
        },
    )

    return {
        "classification": classification,
        "resolution_estimate": resolution,
        "precedent": {
            "confidence": precedent["confidence"],
            "total_matches": len(precedent["matches"]),
            "matches_with_known_duration": len(matches_with_duration),
            "matches": precedent["matches"],
        },
        "text_similar_reports": text_matches,
        "logged_event_id": written["id"],
        "logged_event_source": written["source"],
    }


@app.get("/events/similar")
def similar_events(
    police_station: str,
    event_cause: str,
    corridor: Optional[str] = None,
    limit: int = 5,
    session: Session = Depends(get_session),
):

    return read_similar_events(
        session,
        police_station=police_station,
        event_cause=event_cause,
        corridor=corridor,
        limit=limit,
    )


@app.patch("/events/{event_id}/resolve")
def resolve_event(
    event_id: int, body: ResolveEventRequest, session: Session = Depends(get_session)
):

    event = session.query(Event).filter(Event.id == event_id).first()

    if not event:

        raise HTTPException(status_code=404, detail=f"Event {event_id } not found.")

    if event.closed_datetime is not None:

        raise HTTPException(
            status_code=400,
            detail=f"Event {event_id } already resolved at {event .closed_datetime }.",
        )

    closed_at = body.closed_datetime or datetime.now(timezone.utc)

    if hasattr(closed_at, "tzinfo") and closed_at.tzinfo is not None:

        closed_at = closed_at.replace(tzinfo=None)

    start = event.start_datetime

    if start and hasattr(start, "tzinfo") and (start.tzinfo is not None):

        start = start.replace(tzinfo=None)

    event.closed_datetime = closed_at

    event.status = "closed"

    if start is not None:

        delta = (closed_at - start).total_seconds() / 60

        event.duration_minutes = round(delta, 2) if delta >= 0 else None

    session.commit()

    session.refresh(event)

    return {
        "message": f"Event {event_id } resolved.",
        "event_id": event_id,
        "closed_datetime": event.closed_datetime.isoformat(),
        "duration_minutes": event.duration_minutes,
        "status": event.status,
        "note": "This event now has a real duration and will appear in future precedent lookups for similar events at this station and corridor.",
    }


@app.get("/events/hotspot")
def hotspot_data(session: Session = Depends(get_session)):

    junction_counts = (
        session.query(
            Event.junction,
            Event.latitude,
            Event.longitude,
            func.count(Event.id).label("count"),
        )
        .filter(Event.junction.isnot(None))
        .group_by(Event.junction, Event.latitude, Event.longitude)
        .order_by(func.count(Event.id).desc())
        .limit(100)
        .all()
    )

    corridor_counts = (
        session.query(Event.corridor, func.count(Event.id).label("count"))
        .filter(Event.corridor.isnot(None), Event.corridor != "Non-corridor")
        .group_by(Event.corridor)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    return {
        "junctions": [
            {
                "name": r.junction,
                "lat": r.latitude,
                "lng": r.longitude,
                "count": r.count,
            }
            for r in junction_counts
        ],
        "corridors": [{"name": r.corridor, "count": r.count} for r in corridor_counts],
    }


@app.get("/debug/station")
def debug_station(name: str, session: Session = Depends(get_session)):

    rows = (
        session.query(Event.police_station, func.count(Event.id).label("count"))
        .filter(Event.police_station.ilike(f"%{name }%"))
        .group_by(Event.police_station)
        .all()
    )

    return {
        "query": name,
        "matches": [
            {"police_station": r.police_station, "count": r.count} for r in rows
        ],
    }


@app.get("/debug/cause")
def debug_cause(police_station: str, session: Session = Depends(get_session)):

    rows = (
        session.query(Event.event_cause, func.count(Event.id).label("count"))
        .filter(Event.police_station == police_station)
        .group_by(Event.event_cause)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    return {
        "police_station": police_station,
        "causes": [{"event_cause": r.event_cause, "count": r.count} for r in rows],
    }

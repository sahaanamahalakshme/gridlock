from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from memory.db import get_session
from diversion_engine.src.route_lookup import (
    find_corridor,
    find_route_corridors,
    get_all_corridors,
)
from diversion_engine.src.divert import get_diversion_plan
from classifier_client import classify
from ml_models.resolution_predictor.src.predict import predict as predict_resolution
from diversion_engine.src.directional_divert import get_directional_diversion_plan

diversion_router = APIRouter(prefix="/diversion", tags=["Diversion Simulation"])


class UnplannedDiversionRequest(BaseModel):
    description: str
    incident_lat: float
    incident_lng: float
    hour: Optional[int] = None


class PlannedDiversionRequest(BaseModel):
    event_type: str
    description: Optional[str] = ""
    start_lat: float
    start_lng: float
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    hour: Optional[int] = None


@diversion_router.post("/unplanned")
def simulate_unplanned(
    body: UnplannedDiversionRequest, session: Session = Depends(get_session)
):
    classification = classify(body.description)
    cause = classification["event_cause"]
    severity = classification["severity"]
    affected = find_corridor(body.incident_lat, body.incident_lng)
    hour = body.hour
    if hour is None:
        utc_now = datetime.now(timezone.utc)
        hour = (utc_now.hour + 5) % 24
    plan = get_diversion_plan(
        affected_corridor=affected,
        incident_lat=body.incident_lat,
        incident_lng=body.incident_lng,
        hour=hour,
        cause=cause,
        severity=severity,
        session=session,
    )
    try:
        import app as _app

        resolution = predict_resolution(
            _app._resolution_artifacts,
            {
                "event_cause": cause,
                "corridor": affected or "Non-corridor",
                "priority": severity if severity in ("High", "Low") else "Low",
                "requires_road_closure": False,
                "police_station": "",
            },
        )
    except Exception:
        resolution = {
            "predicted_minutes": None,
            "confidence_band": [None, None],
            "method": "unavailable",
        }
    return {
        "classification": classification,
        "affected_corridor": affected,
        "impact_radius_m": plan["impact_radius_m"],
        "barricade_point": plan["barricade_point"],
        "diversions": plan["diversions"],
        "resolution_estimate": resolution,
        "summary": plan["summary"],
    }


@diversion_router.post("/planned")
def simulate_planned(
    body: PlannedDiversionRequest, session: Session = Depends(get_session)
):
    hour = body.hour
    if hour is None:
        utc_now = datetime.now(timezone.utc)
        hour = (utc_now.hour + 5) % 24
    start_corridor, end_corridor = find_route_corridors(
        body.start_lat,
        body.start_lng,
        body.end_lat or body.start_lat,
        body.end_lng or body.start_lng,
    )
    if body.description and body.description.strip():
        classification = classify(body.description)
        cause = classification["event_cause"]
        severity = classification["severity"]
    else:
        cause = body.event_type
        severity = "High"
        classification = {
            "event_cause": cause,
            "cause_confidence": 1.0,
            "severity": severity,
            "severity_confidence": 1.0,
            "top3_causes": [{"label": cause, "confidence": 1.0}],
        }
    plan = get_diversion_plan(
        affected_corridor=start_corridor,
        incident_lat=body.start_lat,
        incident_lng=body.start_lng,
        hour=hour,
        cause=cause,
        severity=severity,
        session=session,
        end_corridor=end_corridor,
    )
    event_path = [[body.start_lat, body.start_lng]]
    if body.end_lat and body.end_lng:
        event_path.append([body.end_lat, body.end_lng])
    return {
        "classification": classification,
        "start_corridor": start_corridor,
        "end_corridor": end_corridor,
        "event_path": event_path,
        "affected_corridor": start_corridor,
        "impact_radius_m": plan["impact_radius_m"],
        "barricade_point": plan["barricade_point"],
        "diversions": plan["diversions"],
        "summary": plan["summary"],
    }


@diversion_router.get("/corridors")
def corridor_geometry():
    return {"corridors": get_all_corridors()}


class DirectionalDiversionRequest(BaseModel):
    incident_lat: float
    incident_lng: float
    rally_bearing: float
    cause: Optional[str] = "protest"
    severity: Optional[str] = "High"
    affected_corridor: Optional[str] = None
    description: Optional[str] = ""


@diversion_router.post("/directional")
def simulate_directional(
    body: DirectionalDiversionRequest, session: Session = Depends(get_session)
):
    from diversion_engine.src.directional_divert import get_directional_diversion_plan
    from ml_models.bilingual_event_classifier.predict import classify

    if body.description and body.description.strip():
        classification = classify(body.description)
        cause = classification["event_cause"]
        severity = classification["severity"]
    else:
        cause = body.cause
        severity = body.severity
        classification = {
            "event_cause": cause,
            "cause_confidence": 1.0,
            "severity": severity,
            "severity_confidence": 1.0,
            "top3_causes": [],
        }
    plan = get_directional_diversion_plan(
        incident_lat=body.incident_lat,
        incident_lng=body.incident_lng,
        rally_bearing=body.rally_bearing,
        cause=cause,
        severity=severity,
        session=session,
        affected_corridor=body.affected_corridor,
    )
    return {**plan, "classification": classification}

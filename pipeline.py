"""Pipeline script for data processing or inference."""

from pathlib import Path

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from memory.db import init_db, SessionLocal

from memory.confidence import compute_confidence

from memory.memory_store import write_event, read_similar_events

from ml_models.bilingual_event_classifier.predict import classify

from ml_models.resolution_predictor.src.predict import (
    load_artifacts as load_resolution_artifacts,
    predict as predict_resolution,
)

from ml_models.impact_forecaster.src.retrieve import retrieve_similar_event

_ROOT = Path(__file__).resolve().parent

_RESOLUTION_MODEL_DIR = str(_ROOT / "ml_models" / "resolution_predictor" / "models")

_resolution_artifacts = None


def _get_resolution_artifacts():

    global _resolution_artifacts

    if _resolution_artifacts is None:

        _resolution_artifacts = load_resolution_artifacts(
            model_dir=_RESOLUTION_MODEL_DIR
        )

    return _resolution_artifacts


def run_full_pipeline(session: Session, event_input: dict) -> dict:

    description = event_input.get("description", "")

    police_station = event_input["police_station"]

    corridor = event_input.get("corridor")

    classification = classify(description)

    event_cause = classification["event_cause"]

    severity = classification["severity"]

    precedent = read_similar_events(
        session,
        police_station=police_station,
        event_cause=event_cause,
        corridor=corridor,
    )

    matches_with_duration = [
        m for m in precedent["matches"] if m.get("duration_minutes") is not None
    ]

    resolution = predict_resolution(
        _get_resolution_artifacts(),
        {
            "event_cause": event_cause,
            "corridor": corridor or "Non-corridor",
            "priority": severity if severity in ("High", "Low") else "Low",
            "requires_road_closure": event_input.get("requires_road_closure", False),
            "police_station": police_station,
        },
    )

    text_matches = retrieve_similar_event(
        event_cause=event_cause,
        corridor=corridor or "Non-corridor",
        description=description,
        k=3,
    )

    written = write_event(
        session,
        {
            "event_type": event_input.get("event_type", "unplanned"),
            "event_cause": event_cause,
            "status": "active",
            "police_station": police_station,
            "corridor": corridor,
            "zone": event_input.get("zone"),
            "junction": event_input.get("junction"),
            "address": event_input.get("address"),
            "latitude": event_input["latitude"],
            "longitude": event_input["longitude"],
            "priority": severity if severity in ("High", "Low") else None,
            "requires_road_closure": event_input.get("requires_road_closure", False),
            "description": description,
            "start_datetime": event_input.get(
                "start_datetime", datetime.now(timezone.utc)
            ),
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


if __name__ == "__main__":

    import json

    import sys

    if hasattr(sys.stdout, "reconfigure"):

        sys.stdout.reconfigure(encoding="utf-8")

    print("[pipeline] Initialising DB ...")

    init_db()

    print("[pipeline] Opening session ...")

    session = SessionLocal()

    sample = {
        "description": "Vehicle breakdown on Mysore road near toll gate, heavy traffic",
        "corridor": "Mysore Road",
        "police_station": "Kengeri",
        "requires_road_closure": False,
        "latitude": 12.9352,
        "longitude": 77.4977,
    }

    print("[pipeline] Running full pipeline ...")

    result = run_full_pipeline(session, sample)

    session.close()

    print(json.dumps(result, indent=2, default=str))

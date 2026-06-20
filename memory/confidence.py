from sqlalchemy import func
from sqlalchemy.orm import Session
from memory.models import Event

LOW_PRECEDENT_THRESHOLD = 5


def get_precedent_count(session: Session, police_station: str, event_cause: str) -> int:
    return (
        session.query(func.count(Event.id))
        .filter(
            Event.police_station == police_station, Event.event_cause == event_cause
        )
        .scalar()
    )


def confidence_tier(count: int) -> str:
    if count == 0:
        return "no_precedent"
    if count <= 3:
        return "thin"
    if count <= 15:
        return "moderate"
    return "strong"


def compute_confidence(session: Session, police_station: str, event_cause: str) -> dict:
    count = get_precedent_count(session, police_station, event_cause)
    return {
        "precedent_count": count,
        "confidence_tier": confidence_tier(count),
        "low_precedent": count < LOW_PRECEDENT_THRESHOLD,
    }


def enrich_with_confidence(
    session: Session, police_station: str, event_cause: str, matches: list[dict]
) -> list[dict]:

    confidence = compute_confidence(session, police_station, event_cause)
    for m in matches:
        m["confidence"] = confidence
    return matches

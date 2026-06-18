"""
The two operations everything else calls:
  write_event()         - log a new event (live, from the classifier/forms)
  read_similar_events()  - fetch past precedent for a given station+cause,
                            with confidence attached

api.py wraps these as HTTP endpoints. Person C's retrieval model
(impact_forecaster) should call read_similar_events() instead of holding
its own static in-memory list - that's what makes "the system learns from
what just happened" literally true rather than a slide claim.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from models import Event
from confidence import compute_confidence


def _compute_duration_minutes(start, end):
    if start is None or end is None:
        return None
    delta = (end - start).total_seconds() / 60
    return delta if delta >= 0 else None  # negative = bad timestamps, not a real duration


def write_event(session: Session, event_data: dict) -> dict:
    """
    event_data keys expected: event_type, event_cause, status, police_station,
    corridor, zone, junction, address, latitude, longitude, priority,
    requires_road_closure, description, start_datetime, end_datetime (optional),
    closed_datetime (optional), resolved_datetime (optional).
    source is always set to 'live' here - seed_historical.py is the only
    place 'historical' rows get created.
    """
    end_for_duration = (
        event_data.get("resolved_datetime")
        or event_data.get("closed_datetime")
        or event_data.get("end_datetime")
    )
    duration_minutes = _compute_duration_minutes(
        event_data.get("start_datetime"), end_for_duration
    )

    event = Event(
        source_id=None,
        event_type=event_data["event_type"],
        event_cause=event_data["event_cause"],
        status=event_data.get("status", "active"),
        source="live",
        police_station=event_data["police_station"],
        corridor=event_data.get("corridor"),
        zone=event_data.get("zone"),
        junction=event_data.get("junction"),
        address=event_data.get("address"),
        latitude=event_data["latitude"],
        longitude=event_data["longitude"],
        priority=event_data.get("priority"),
        requires_road_closure=event_data.get("requires_road_closure", False),
        description=event_data.get("description"),
        start_datetime=event_data["start_datetime"],
        end_datetime=event_data.get("end_datetime"),
        closed_datetime=event_data.get("closed_datetime"),
        resolved_datetime=event_data.get("resolved_datetime"),
        duration_minutes=duration_minutes,
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    result = event.to_dict()
    result["confidence"] = compute_confidence(session, event.police_station, event.event_cause)
    return result


def read_similar_events(
    session: Session,
    police_station: str,
    event_cause: str,
    corridor: str = None,
    limit: int = 5,
) -> dict:
    """
    Returns the most recent precedent events for this station+cause,
    narrowed by corridor when given and when that narrower query still
    returns something - falls back to the station+cause level otherwise,
    since corridor is missing on 20 historical rows and a hard corridor
    filter would silently drop legitimate matches.
    """
    base_query = session.query(Event).filter(
        Event.police_station == police_station, Event.event_cause == event_cause
    )

    matches = []
    if corridor:
        corridor_matches = (
            base_query.filter(Event.corridor == corridor)
            .order_by(Event.start_datetime.desc())
            .limit(limit)
            .all()
        )
        matches = corridor_matches

    if not matches:
        matches = base_query.order_by(Event.start_datetime.desc()).limit(limit).all()

    confidence = compute_confidence(session, police_station, event_cause)

    return {
        "matches": [m.to_dict() for m in matches],
        "confidence": confidence,
    }
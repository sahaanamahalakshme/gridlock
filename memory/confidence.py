"""

Confidence-aware memory: turns a raw precedent count into a tier the

frontend can show next to a retrieval result, so SENTRY visibly says

"thin precedent" instead of quietly returning a confident-looking number

backed by one record (or none).



Computed live via COUNT(*) rather than a precomputed/materialized table.

That's a deliberate tradeoff: at ~8,000-15,000 rows a COUNT with the

(police_station, event_cause) index is sub-millisecond, and a live count

can never go stale the way a cached one would the moment a new event gets

written mid-demo.



Thresholds below come from the real distribution across the 509 distinct

(police_station, event_cause) pairs actually observed in the historical

data (54 stations x 17 causes = 918 possible pairs, so 409 of those pairs

have ZERO precedent - "no_precedent" is the common case, not an edge case):

  count == 0        -> no_precedent

  1  to 3            -> thin        (~41% of observed pairs)

  4  to 15           -> moderate

  16+                -> strong       (e.g. Yelahanka + vehicle_breakdown = 251)

"""

from sqlalchemy import func

from sqlalchemy.orm import Session

from memory.models import Event


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
    }

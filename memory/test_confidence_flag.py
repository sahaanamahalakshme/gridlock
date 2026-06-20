import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from memory.db import SessionLocal
from memory.models import Event
from memory.confidence import compute_confidence
from sqlalchemy import distinct

EXPECTED_LOW_PRECEDENT_PAIRS = 248
EXPECTED_TOTAL_PAIRS = 509


def run():
    session = SessionLocal()

    pairs = session.query(distinct(Event.police_station), Event.event_cause).all()
    pairs = sorted(set(pairs))

    low_precedent_count = 0
    tier_breakdown = {"no_precedent": 0, "thin": 0, "moderate": 0, "strong": 0}
    strongest = (None, None, 0)

    for police_station, event_cause in pairs:
        conf = compute_confidence(session, police_station, event_cause)
        tier_breakdown[conf["confidence_tier"]] += 1
        if conf["low_precedent"]:
            low_precedent_count += 1
        if conf["precedent_count"] > strongest[2]:
            strongest = (police_station, event_cause, conf["precedent_count"])

    session.close()

    print(f"distinct (police_station, event_cause) pairs in DB: {len(pairs)}")
    print(
        f"  (raw CSV had {EXPECTED_TOTAL_PAIRS} - small drop is expected, from the 2 dropped rows)"
    )
    print(
        f"low_precedent pairs (count<5): {low_precedent_count}  "
        f"({low_precedent_count/len(pairs):.1%})"
    )
    print(
        f"  (reference: {EXPECTED_LOW_PRECEDENT_PAIRS}/{EXPECTED_TOTAL_PAIRS} = 48.7% from raw CSV)"
    )
    print(f"tier breakdown: {tier_breakdown}")
    print(
        f"strongest precedent: {strongest[0]} + {strongest[1]} = {strongest[2]} prior events"
    )


if __name__ == "__main__":
    run()

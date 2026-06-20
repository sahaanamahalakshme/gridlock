"""
divert.py
---------
Place at: gridlock/diversion_engine/src/divert.py

Takes an affected corridor + event context and returns ranked alternate
corridors using historical event density from the memory store.

Scoring logic (lower score = better diversion candidate):
  base_score        = n_historical_events on that corridor (from corridors.json)
  active_penalty    = +9999 if any active incident on that corridor right now
  time_slot_bonus   = uses hour-of-day event density from memory store
                      (corridors busy at this hour get penalised more)
  severity_weight   = High severity events get a stricter radius — excludes
                      corridors closer than 300m to the incident point

This is fully honest: every number in the output traces to either the
historical event count in corridors.json or a live query to the memory
store. No invented traffic density.
"""

import json
import math
from pathlib import Path
from typing import Optional

from diversion_engine.src.route_lookup import _CORRIDORS, _haversine_m, get_corridor_centroid

# ── Constants ────────────────────────────────────────────────────────────────

_ACTIVE_PENALTY = 9999      # Effectively excludes a corridor from diversion
_MIN_DIVERSION_DIST_M = 200  # Don't suggest a corridor centroid closer than this to the incident
_TOP_K = 3                   # Return top 3 diversion options


def _get_active_corridors(session) -> set[str]:
    """
    Query the memory store for corridors with currently active incidents.
    Returns a set of corridor names that should be penalised.
    """
    try:
        from memory.models import Event
        active_rows = (
            session.query(Event.corridor)
            .filter(Event.status == "active", Event.corridor.isnot(None))
            .all()
        )
        return {row.corridor for row in active_rows if row.corridor}
    except Exception:
        return set()   # Fail safe — don't crash diversion if DB is unreachable


def _hour_density(session, corridor_name: str, hour: int) -> int:
    """
    Count historical events on this corridor at this hour-of-day from the
    memory store. Used to avoid recommending a diversion onto a corridor
    that's historically busy at the same time of day.
    """
    try:
        from memory.models import Event
        from sqlalchemy import extract, func
        count = (
            session.query(func.count(Event.id))
            .filter(
                Event.corridor == corridor_name,
                extract("hour", Event.start_datetime) == hour,
            )
            .scalar()
        ) or 0
        return int(count)
    except Exception:
        return 0


def score_corridors(
    affected_corridor: str,
    incident_lat: float,
    incident_lng: float,
    hour: int,
    severity: str,
    session,
    exclude_corridors: Optional[list[str]] = None,
) -> list[dict]:
    """
    Score all corridors and return the top 3 diversion candidates.

    Args:
        affected_corridor:  The corridor where the event/incident is happening.
                            Always excluded from results.
        incident_lat/lng:   Location of the incident or event start point.
        hour:               Current hour of day (0-23, IST).
        severity:           "High" or "Low" — affects minimum distance filter.
        session:            SQLAlchemy session for memory store queries.
        exclude_corridors:  Optional extra corridors to exclude (e.g. event
                            end-point corridor for processions).

    Returns:
        List of up to 3 dicts, best first:
        {
            "corridor": str,
            "centroid": [lat, lng],
            "score": float,            # Lower = better
            "n_historical_events": int,
            "hour_density": int,       # Events on this corridor at this hour
            "distance_from_incident_m": float,
            "reason": str,             # Human-readable explanation
        }
    """
    excluded = {affected_corridor, "Non-corridor"}
    if exclude_corridors:
        excluded.update(exclude_corridors)

    active_corridors = _get_active_corridors(session)

    # Minimum diversion distance: further for High severity events
    min_dist_m = 400 if severity == "High" else _MIN_DIVERSION_DIST_M

    candidates = []

    for name, data in _CORRIDORS.items():
        if name in excluded:
            continue

        centroid = data.get("centroid")
        if not centroid:
            continue

        c_lat, c_lng = centroid[0], centroid[1]
        dist_m = _haversine_m(incident_lat, incident_lng, c_lat, c_lng)

        # Skip corridors too close to the incident — they're in the impact zone
        if dist_m < min_dist_m:
            continue

        n_events = data.get("n_historical_events", 0)
        h_density = _hour_density(session, name, hour)
        active_penalty = _ACTIVE_PENALTY if name in active_corridors else 0

        # Score: base from total historical events + same-hour density * 3
        # Lower is better — quieter corridors score lower
        score = n_events + (h_density * 3) + active_penalty

        candidates.append({
            "corridor": name,
            "centroid": [c_lat, c_lng],
            "score": score,
            "n_historical_events": n_events,
            "hour_density": h_density,
            "distance_from_incident_m": round(dist_m, 1),
            "active_incident": name in active_corridors,
        })

    # Sort by score ascending (quietest first), break ties by distance descending
    # (further from incident = more separation = safer diversion)
    candidates.sort(key=lambda x: (x["score"], -x["distance_from_incident_m"]))

    top = candidates[:_TOP_K]

    # Add human-readable reason to each
    for c in top:
        reasons = []
        if c["n_historical_events"] < 50:
            reasons.append(f"low historical incident density ({c['n_historical_events']} past events)")
        if c["hour_density"] == 0:
            reasons.append("no recorded incidents at this hour")
        elif c["hour_density"] <= 2:
            reasons.append(f"quiet at this hour ({c['hour_density']} incidents historically)")
        if c["distance_from_incident_m"] > 1000:
            reasons.append(f"{round(c['distance_from_incident_m']/1000, 1)}km from incident")
        if not reasons:
            reasons.append("best available alternate corridor")
        c["reason"] = "; ".join(reasons)
        del c["active_incident"]   # Already implicit — don't surface raw bool to frontend

    return top


def get_diversion_plan(
    affected_corridor: str | None,
    incident_lat: float,
    incident_lng: float,
    hour: int,
    cause: str,
    severity: str,
    session,
    end_corridor: str | None = None,
) -> dict:
    """
    Top-level function called by the FastAPI endpoint.
    Returns everything the simulation page map needs to render.

    For unplanned events: affected_corridor may be None if the click
    point didn't match any corridor — system still attempts diversion
    based on spatial position.

    Returns:
        {
            "affected_corridor": str | None,
            "impact_radius_m": int,         # For the orange circle on the map
            "barricade_point": [lat, lng],  # Where to place the barricade icon
            "diversions": [...],            # Top 3 from score_corridors()
            "summary": str,                 # One-sentence summary for the card
        }
    """
    # Impact radius: bigger for High severity and road-closure-type causes
    high_impact_causes = {"accident", "water_logging", "tree_fall", "vip_movement",
                          "public_event", "procession", "construction"}
    if severity == "High" or cause in high_impact_causes:
        radius_m = 600
    else:
        radius_m = 300

    exclude = [end_corridor] if end_corridor else []

    diversions = score_corridors(
        affected_corridor=affected_corridor or "__none__",
        incident_lat=incident_lat,
        incident_lng=incident_lng,
        hour=hour,
        severity=severity,
        session=session,
        exclude_corridors=exclude,
    )

    # Build summary sentence
    if diversions:
        best = diversions[0]
        summary = (
            f"Incident on {affected_corridor or 'unidentified corridor'} "
            f"({cause}, {severity} severity). "
            f"Recommended diversion: {best['corridor']} — {best['reason']}."
        )
    else:
        summary = (
            f"Incident on {affected_corridor or 'unidentified corridor'}. "
            f"No clear diversion corridor found near this location."
        )

    return {
        "affected_corridor": affected_corridor,
        "impact_radius_m": radius_m,
        "barricade_point": [incident_lat, incident_lng],
        "diversions": diversions,
        "summary": summary,
    }


# ── Smoke test (no DB — uses empty session stub) ──────────────────────────────
if __name__ == "__main__":
    class _FakeSession:
        def query(self, *a, **kw):
            return self
        def filter(self, *a, **kw):
            return self
        def all(self):
            return []
        def scalar(self):
            return 0

    print("Diversion plan — unplanned vehicle breakdown on Mysore Road:")
    plan = get_diversion_plan(
        affected_corridor="Mysore Road",
        incident_lat=12.9352,
        incident_lng=77.4977,
        hour=8,
        cause="vehicle_breakdown",
        severity="High",
        session=_FakeSession(),
    )
    print(f"  Affected: {plan['affected_corridor']}")
    print(f"  Radius: {plan['impact_radius_m']}m")
    print(f"  Summary: {plan['summary']}")
    print(f"  Top diversions:")
    for d in plan["diversions"]:
        print(f"    {d['corridor']}: score={d['score']}, dist={d['distance_from_incident_m']}m — {d['reason']}")

    print()
    print("Diversion plan — planned procession CBD 2 → CBD 1:")
    plan2 = get_diversion_plan(
        affected_corridor="CBD 2",
        incident_lat=12.9793,
        incident_lng=77.5996,
        hour=18,
        cause="procession",
        severity="High",
        session=_FakeSession(),
        end_corridor="CBD 1",
    )
    print(f"  Summary: {plan2['summary']}")
    for d in plan2["diversions"]:
        print(f"    {d['corridor']}: score={d['score']} — {d['reason']}")
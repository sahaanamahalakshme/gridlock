import json
import math
from pathlib import Path
from typing import Optional
from diversion_engine.src.route_lookup import (
    _CORRIDORS,
    _haversine_m,
    get_corridor_centroid,
)

_ACTIVE_PENALTY = 9999
_MIN_DIVERSION_DIST_M = 200
_TOP_K = 3


def _get_active_corridors(session) -> set[str]:
    try:
        from memory.models import Event

        active_rows = (
            session.query(Event.corridor)
            .filter(Event.status == "active", Event.corridor.isnot(None))
            .all()
        )
        return {row.corridor for row in active_rows if row.corridor}
    except Exception:
        return set()


def _hour_density(session, corridor_name: str, hour: int) -> int:
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
            or 0
        )
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
    excluded = {affected_corridor, "Non-corridor"}
    if exclude_corridors:
        excluded.update(exclude_corridors)
    active_corridors = _get_active_corridors(session)
    min_dist_m = 400 if severity == "High" else _MIN_DIVERSION_DIST_M
    candidates = []
    for name, data in _CORRIDORS.items():
        if name in excluded:
            continue
        centroid = data.get("centroid")
        if not centroid:
            continue
        c_lat, c_lng = (centroid[0], centroid[1])
        dist_m = _haversine_m(incident_lat, incident_lng, c_lat, c_lng)
        if dist_m < min_dist_m:
            continue
        n_events = data.get("n_historical_events", 0)
        h_density = _hour_density(session, name, hour)
        active_penalty = _ACTIVE_PENALTY if name in active_corridors else 0
        score = n_events + h_density * 3 + active_penalty
        candidates.append(
            {
                "corridor": name,
                "centroid": [c_lat, c_lng],
                "score": score,
                "n_historical_events": n_events,
                "hour_density": h_density,
                "distance_from_incident_m": round(dist_m, 1),
                "active_incident": name in active_corridors,
            }
        )
    candidates.sort(key=lambda x: (x["score"], -x["distance_from_incident_m"]))
    top = candidates[:_TOP_K]
    for c in top:
        reasons = []
        if c["n_historical_events"] < 50:
            reasons.append(
                f"low historical incident density ({c['n_historical_events']} past events)"
            )
        if c["hour_density"] == 0:
            reasons.append("no recorded incidents at this hour")
        elif c["hour_density"] <= 2:
            reasons.append(
                f"quiet at this hour ({c['hour_density']} incidents historically)"
            )
        if c["distance_from_incident_m"] > 1000:
            reasons.append(
                f"{round(c['distance_from_incident_m'] / 1000, 1)}km from incident"
            )
        if not reasons:
            reasons.append("best available alternate corridor")
        c["reason"] = "; ".join(reasons)
        del c["active_incident"]
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
    high_impact_causes = {
        "accident",
        "water_logging",
        "tree_fall",
        "vip_movement",
        "public_event",
        "procession",
        "construction",
    }
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
    if diversions:
        best = diversions[0]
        summary = f"Incident on {affected_corridor or 'unidentified corridor'} ({cause}, {severity} severity). Recommended diversion: {best['corridor']} — {best['reason']}."
    else:
        summary = f"Incident on {affected_corridor or 'unidentified corridor'}. No clear diversion corridor found near this location."
    return {
        "affected_corridor": affected_corridor,
        "impact_radius_m": radius_m,
        "barricade_point": [incident_lat, incident_lng],
        "diversions": diversions,
        "summary": summary,
    }


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
        print(
            f"    {d['corridor']}: score={d['score']}, dist={d['distance_from_incident_m']}m — {d['reason']}"
        )
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

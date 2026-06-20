import math
from pathlib import Path
import json

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "corridors.json"


def _load_corridors():
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_CORRIDORS = _load_corridors()


def _haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = (math.radians(lat1), math.radians(lat2))
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _bearing(from_lat, from_lng, to_lat, to_lng):
    dy = to_lat - from_lat
    dx = to_lng - from_lng
    angle = math.degrees(math.atan2(dy, dx))
    return (90 - angle) % 360


def _angular_diff(a, b):
    diff = (b - a + 180) % 360 - 180
    return diff


def _approach_quadrant(corridor_bearing_from_incident, rally_bearing):
    approach_bearing = (corridor_bearing_from_incident + 180) % 360
    diff = _angular_diff(rally_bearing, approach_bearing)
    if abs(diff) <= 45:
        return "tail_on"
    elif abs(diff) >= 135:
        return "head_on"
    elif diff > 0:
        return "cross_right"
    else:
        return "cross_left"


def _safe_side_bearing(quadrant, rally_bearing):
    if quadrant == "head_on":
        return (rally_bearing + 90) % 360
    elif quadrant == "tail_on":
        return (rally_bearing + 90) % 360
    elif quadrant == "cross_left":
        return (rally_bearing - 90) % 360
    elif quadrant == "cross_right":
        return (rally_bearing + 90) % 360
    return rally_bearing


QUADRANT_LABELS = {
    "head_on": "Head-on (approaching rally directly)",
    "tail_on": "Tail-on (behind the rally)",
    "cross_left": "Crossing from left",
    "cross_right": "Crossing from right",
}
QUADRANT_INSTRUCTION = {
    "head_on": "STOP — rally approaching. Divert immediately.",
    "tail_on": "Do not follow rally. Take diversion before next junction.",
    "cross_left": "Rally crossing ahead. Divert before the crossing point.",
    "cross_right": "Rally crossing ahead. Divert before the crossing point.",
}


def get_directional_diversion_plan(
    incident_lat: float,
    incident_lng: float,
    rally_bearing: float,
    cause: str,
    severity: str,
    session,
    affected_corridor: str = None,
) -> dict:

    active_corridors = _get_active_corridors(session)
    corridor_info = {}
    for name, data in _CORRIDORS.items():
        if name in ("Non-corridor", affected_corridor):
            continue
        centroid = data.get("centroid")
        if not centroid:
            continue
        c_lat, c_lng = (centroid[0], centroid[1])
        dist_m = _haversine_m(incident_lat, incident_lng, c_lat, c_lng)
        if dist_m < 200:
            continue
        brg = _bearing(incident_lat, incident_lng, c_lat, c_lng)
        quadrant = _approach_quadrant(brg, rally_bearing)
        safe_dir = _safe_side_bearing(quadrant, rally_bearing)
        safe_angle_diff = abs(_angular_diff(brg, (safe_dir + 180) % 360))
        n_events = data.get("n_historical_events", 0)
        active_pen = 5000 if name in active_corridors else 0
        score = safe_angle_diff * 2 + n_events + active_pen
        corridor_info[name] = {
            "corridor": name,
            "centroid": [c_lat, c_lng],
            "bearing_from_incident": round(brg, 1),
            "quadrant": quadrant,
            "distance_from_incident_m": round(dist_m, 1),
            "n_historical_events": n_events,
            "score": round(score, 1),
            "active_incident": name in active_corridors,
        }
    groups = {q: [] for q in ["head_on", "tail_on", "cross_left", "cross_right"]}
    for name, info in corridor_info.items():
        groups[info["quadrant"]].append(info)
    result_groups = {}
    for quadrant, corridors in groups.items():
        corridors_sorted = sorted(corridors, key=lambda x: x["score"])
        best = corridors_sorted[0] if corridors_sorted else None
        if best:
            reasons = []
            if best["n_historical_events"] < 50:
                reasons.append(
                    f"low congestion history ({best['n_historical_events']} events)"
                )
            if not best["active_incident"]:
                reasons.append("no active incident")
            if best["distance_from_incident_m"] > 800:
                reasons.append(
                    f"{round(best['distance_from_incident_m'] / 1000, 1)}km from rally"
                )
            best["reason"] = (
                "; ".join(reasons) if reasons else "best available alternate"
            )
        approach_names = [c["corridor"] for c in corridors_sorted]
        result_groups[quadrant] = {
            "label": QUADRANT_LABELS[quadrant],
            "instruction": QUADRANT_INSTRUCTION[quadrant],
            "approach_corridors": approach_names[:3],
            "diversion": best,
        }
    dirs = [
        "North",
        "North-East",
        "East",
        "South-East",
        "South",
        "South-West",
        "West",
        "North-West",
    ]
    direction_label = dirs[round(rally_bearing / 45) % 8]
    high_impact = {"accident", "public_event", "procession", "vip_movement", "protest"}
    radius_m = 700 if severity == "High" or cause in high_impact else 400
    head_on_diversion = result_groups["head_on"]["diversion"]
    summary = f"Rally moving {direction_label}. Traffic approaching head-on: divert via {(head_on_diversion['corridor'] if head_on_diversion else 'no corridor found')}. Cross-traffic: see directional plan below."
    return {
        "rally_bearing": rally_bearing,
        "rally_direction_label": direction_label,
        "impact_radius_m": radius_m,
        "barricade_point": [incident_lat, incident_lng],
        "approach_groups": result_groups,
        "summary": summary,
    }


def _get_active_corridors(session) -> set:
    try:
        from memory.models import Event

        rows = (
            session.query(Event.corridor)
            .filter(Event.status == "active", Event.corridor.isnot(None))
            .all()
        )
        return {r.corridor for r in rows if r.corridor}
    except Exception:
        return set()


if __name__ == "__main__":

    class _FakeSession:

        def query(self, *a):
            return self

        def filter(self, *a):
            return self

        def all(self):
            return []

    print("Rally moving NORTH from Cubbon Park area:")
    plan = get_directional_diversion_plan(
        incident_lat=12.9793,
        incident_lng=77.5996,
        rally_bearing=0,
        cause="protest",
        severity="High",
        session=_FakeSession(),
        affected_corridor="CBD 2",
    )
    print(f"Direction: {plan['rally_direction_label']}")
    print(f"Summary: {plan['summary']}")
    print()
    for q, g in plan["approach_groups"].items():
        div = g["diversion"]
        print(f"  {q.upper():15s}: {g['instruction']}")
        print(f"    Approach corridors: {g['approach_corridors']}")
        print(f"    Divert to: {(div['corridor'] if div else 'None')}")
        print()

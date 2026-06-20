"""
directional_divert.py
---------------------
Place at: gridlock/diversion_engine/src/directional_divert.py

Replaces the flat "best corridor" logic in divert.py with proper
directional traffic management:

  Rally/event moves in direction D (e.g. North).
  Traffic approaching from each compass quadrant gets its OWN diversion
  recommendation — not a single diversion for everyone.

  The four approach quadrants relative to the rally:
    PARALLEL_WITH   — same direction as rally, behind it → hold / detour
    PARALLEL_AGAINST — head-on into rally → divert sideways urgently
    PERPENDICULAR_LEFT  — crossing rally's path from left → divert before crossing
    PERPENDICULAR_RIGHT — crossing rally's path from right → divert before crossing

  Each quadrant gets the best available corridor on the SAFE SIDE —
  i.e. a corridor that does NOT cross the rally path.
"""

import math
from pathlib import Path
import json

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "corridors.json"

def _load_corridors():
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

_CORRIDORS = _load_corridors()


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _haversine_m(lat1, lng1, lat2, lng2):
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _bearing(from_lat, from_lng, to_lat, to_lng):
    """Compass bearing in degrees (0=N, 90=E, 180=S, 270=W)."""
    dy = to_lat - from_lat
    dx = to_lng - from_lng
    angle = math.degrees(math.atan2(dy, dx))
    return (90 - angle) % 360


def _angular_diff(a, b):
    """Signed angular difference a→b, range -180 to +180."""
    diff = (b - a + 180) % 360 - 180
    return diff


def _approach_quadrant(corridor_bearing_from_incident, rally_bearing):
    """
    Given a corridor's bearing FROM the incident point, and the rally's
    travel bearing, classify traffic approaching from that corridor.

    Returns one of:
        'head_on'       — traffic coming straight at the rally (most urgent)
        'tail_on'       — traffic behind the rally going same direction
        'cross_left'    — traffic crossing rally's path from the left
        'cross_right'   — traffic crossing rally's path from the right
    """
    # Bearing FROM the corridor TO the incident (approaching direction)
    approach_bearing = (corridor_bearing_from_incident + 180) % 360

    # How different is this approach from the rally's travel direction?
    diff = _angular_diff(rally_bearing, approach_bearing)

    if abs(diff) <= 45:
        return 'tail_on'          # coming from behind, same direction as rally
    elif abs(diff) >= 135:
        return 'head_on'          # coming head-on into rally
    elif diff > 0:
        return 'cross_right'      # crossing from right
    else:
        return 'cross_left'       # crossing from left


def _safe_side_bearing(quadrant, rally_bearing):
    """
    Returns the compass bearing that is the SAFE diversion direction
    for each approach quadrant.

    head_on   → divert to EITHER side (perpendicular to rally)
    tail_on   → hold back or use parallel detour (perpendicular to rally)
    cross_left  → divert BEFORE the crossing point, back left
    cross_right → divert BEFORE the crossing point, back right
    """
    if quadrant == 'head_on':
        # Best diversion: either side, pick corridor closest to perpendicular-right
        return (rally_bearing + 90) % 360
    elif quadrant == 'tail_on':
        # Detour: send left or right well before the rally's tail
        return (rally_bearing + 90) % 360
    elif quadrant == 'cross_left':
        # Send back left (away from crossing)
        return (rally_bearing - 90) % 360
    elif quadrant == 'cross_right':
        # Send back right (away from crossing)
        return (rally_bearing + 90) % 360
    return rally_bearing


QUADRANT_LABELS = {
    'head_on':    'Head-on (approaching rally directly)',
    'tail_on':    'Tail-on (behind the rally)',
    'cross_left': 'Crossing from left',
    'cross_right': 'Crossing from right',
}

QUADRANT_INSTRUCTION = {
    'head_on':    'STOP — rally approaching. Divert immediately.',
    'tail_on':    'Do not follow rally. Take diversion before next junction.',
    'cross_left': 'Rally crossing ahead. Divert before the crossing point.',
    'cross_right': 'Rally crossing ahead. Divert before the crossing point.',
}


# ── Main function ─────────────────────────────────────────────────────────────

def get_directional_diversion_plan(
    incident_lat: float,
    incident_lng: float,
    rally_bearing: float,          # degrees, 0=N, 90=E, 180=S, 270=W
    cause: str,
    severity: str,
    session,
    affected_corridor: str = None,
) -> dict:
    """
    Returns per-approach-direction diversion recommendations.

    Args:
        incident_lat/lng:  Where the rally/event starts.
        rally_bearing:     Direction the rally is moving (compass degrees).
        cause:             Event cause string.
        severity:          "High" or "Low".
        session:           SQLAlchemy session.
        affected_corridor: Primary corridor of the rally (excluded from diversions).

    Returns:
        {
            "rally_bearing": float,
            "rally_direction_label": str,     # e.g. "North"
            "impact_radius_m": int,
            "barricade_point": [lat, lng],
            "approach_groups": {
                "head_on": {
                    "label": str,
                    "instruction": str,
                    "corridors": [list of approach corridors from this direction],
                    "diversion": { corridor dict } | None
                },
                "tail_on": { ... },
                "cross_left": { ... },
                "cross_right": { ... },
            },
            "summary": str,
        }
    """
    # Get active corridors from memory store
    active_corridors = _get_active_corridors(session)

    # Build per-corridor metadata: bearing from incident, quadrant, distance
    corridor_info = {}
    for name, data in _CORRIDORS.items():
        if name in ("Non-corridor", affected_corridor):
            continue
        centroid = data.get("centroid")
        if not centroid:
            continue
        c_lat, c_lng = centroid[0], centroid[1]
        dist_m = _haversine_m(incident_lat, incident_lng, c_lat, c_lng)
        if dist_m < 200:
            continue  # Too close to incident to be a usable diversion

        brg = _bearing(incident_lat, incident_lng, c_lat, c_lng)
        quadrant = _approach_quadrant(brg, rally_bearing)
        safe_dir = _safe_side_bearing(quadrant, rally_bearing)

        # Score: lower is better diversion
        # Prefer corridors that are on the correct safe side + low event density
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

    # Group corridors by quadrant and find best diversion per quadrant
    groups = {q: [] for q in ['head_on', 'tail_on', 'cross_left', 'cross_right']}
    for name, info in corridor_info.items():
        groups[info["quadrant"]].append(info)

    result_groups = {}
    for quadrant, corridors in groups.items():
        corridors_sorted = sorted(corridors, key=lambda x: x["score"])
        best = corridors_sorted[0] if corridors_sorted else None

        if best:
            # Build human reason string
            reasons = []
            if best["n_historical_events"] < 50:
                reasons.append(f"low congestion history ({best['n_historical_events']} events)")
            if not best["active_incident"]:
                reasons.append("no active incident")
            if best["distance_from_incident_m"] > 800:
                reasons.append(f"{round(best['distance_from_incident_m']/1000, 1)}km from rally")
            best["reason"] = "; ".join(reasons) if reasons else "best available alternate"

        # Which corridors approach from this direction
        approach_names = [c["corridor"] for c in corridors_sorted]

        result_groups[quadrant] = {
            "label": QUADRANT_LABELS[quadrant],
            "instruction": QUADRANT_INSTRUCTION[quadrant],
            "approach_corridors": approach_names[:3],  # Top 3 approach corridors
            "diversion": best,
        }

    # Rally direction label
    dirs = ['North', 'North-East', 'East', 'South-East',
            'South', 'South-West', 'West', 'North-West']
    direction_label = dirs[round(rally_bearing / 45) % 8]

    # Impact radius
    high_impact = {"accident", "public_event", "procession", "vip_movement", "protest"}
    radius_m = 700 if severity == "High" or cause in high_impact else 400

    # One-sentence summary
    head_on_diversion = result_groups["head_on"]["diversion"]
    summary = (
        f"Rally moving {direction_label}. "
        f"Traffic approaching head-on: divert via {head_on_diversion['corridor'] if head_on_diversion else 'no corridor found'}. "
        f"Cross-traffic: see directional plan below."
    )

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


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    class _FakeSession:
        def query(self, *a): return self
        def filter(self, *a): return self
        def all(self): return []

    print("Rally moving NORTH from Cubbon Park area:")
    plan = get_directional_diversion_plan(
        incident_lat=12.9793, incident_lng=77.5996,
        rally_bearing=0,  # North
        cause="protest", severity="High",
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
        print(f"    Divert to: {div['corridor'] if div else 'None'}")
        print()
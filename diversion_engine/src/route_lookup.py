import json
import math
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "corridors.json"


def _load_corridors() -> dict:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_CORRIDORS: dict = _load_corridors()
_MAX_DIST_DEGREES = 0.0045


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = (math.radians(lat1), math.radians(lat2))
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _point_to_segment_dist(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> tuple[float, float, float]:
    dx, dy = (bx - ax, by - ay)
    if dx == 0 and dy == 0:
        return (_haversine_m(px, py, ax, ay), ax, ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    nx, ny = (ax + t * dx, ay + t * dy)
    return (_haversine_m(px, py, nx, ny), nx, ny)


def _nearest_on_polyline(lat: float, lng: float, points: list[list[float]]) -> float:
    if len(points) == 0:
        return math.inf
    if len(points) == 1:
        return _haversine_m(lat, lng, points[0][0], points[0][1])
    best = math.inf
    for i in range(len(points) - 1):
        a, b = (points[i], points[i + 1])
        dist, _, _ = _point_to_segment_dist(lat, lng, a[0], a[1], b[0], b[1])
        if dist < best:
            best = dist
    return best


def find_corridor(lat: float, lng: float, max_dist_m: float = 500.0) -> str | None:
    best_name: str | None = None
    best_dist: float = math.inf
    for name, data in _CORRIDORS.items():
        if name == "Non-corridor":
            continue
        points = data.get("points", [])
        if not points:
            continue
        dist = _nearest_on_polyline(lat, lng, points)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    if best_dist > max_dist_m:
        return None
    return best_name


def find_route_corridors(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    max_dist_m: float = 500.0,
) -> tuple[str | None, str | None]:
    start_corridor = find_corridor(start_lat, start_lng, max_dist_m)
    end_corridor = find_corridor(end_lat, end_lng, max_dist_m)
    return (start_corridor, end_corridor)


def get_corridor_centroid(name: str) -> tuple[float, float] | None:
    data = _CORRIDORS.get(name)
    if not data:
        return None
    c = data.get("centroid")
    if not c:
        return None
    return (c[0], c[1])


def get_all_corridors() -> list[dict]:
    return [
        {
            "name": name,
            "centroid": data.get("centroid"),
            "n_historical_events": data.get("n_historical_events", 0),
            "points": data.get("points", []),
        }
        for name, data in _CORRIDORS.items()
        if name != "Non-corridor"
    ]


if __name__ == "__main__":
    tests = [
        (12.9081, 77.6476, "near Silk Board / ORR East 1"),
        (12.9793, 77.5996, "Cubbon Park area / CBD 2"),
        (12.9352, 77.4977, "Kengeri / Mysore Road"),
        (13.04, 77.5181, "Yeshwanthpur / Tumkur Road"),
        (13.0, 77.7, "should be None — no corridor nearby"),
    ]
    print("find_corridor smoke test")
    print("-" * 50)
    for lat, lng, label in tests:
        result = find_corridor(lat, lng)
        print(f"  ({lat}, {lng})  [{label}]")
        print(f"    → {result}")
    print()
    print("find_route_corridors smoke test")
    print("-" * 50)
    start, end = find_route_corridors(12.9793, 77.5996, 12.9716, 77.5946)
    print(f"  start corridor: {start}")
    print(f"  end corridor:   {end}")

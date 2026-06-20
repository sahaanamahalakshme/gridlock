ROUTING_MAP = {
    "pot_holes": "bbmp",
    "construction": "bbmp",
    "road_conditions": "bbmp",
    "water_logging": "bwssb",
    "public_event": "organiser",
    "procession": "organiser",
    "vip_movement": "organiser",
    "protest": "organiser",
    "vehicle_breakdown": "police",
    "accident": "police",
    "tree_fall": "police",
    "congestion": "police",
    "debris": "police",
    "fog / low visibility": "police",
}

AMBIGUOUS_CAUSES = {"others", "test_demo"}

VALID_AGENCIES = {"police", "bbmp", "bwssb", "organiser"}


def route_event(event_cause: str) -> dict:
    normalized = event_cause.strip().lower()

    if normalized in AMBIGUOUS_CAUSES:
        return {"routing_agency": "police", "is_ambiguous": True}

    agency = ROUTING_MAP.get(normalized)
    if agency is None:
        return {"routing_agency": "police", "is_ambiguous": True}

    return {"routing_agency": agency, "is_ambiguous": False}

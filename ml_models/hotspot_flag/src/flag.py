"""
flag.py
-------
Runtime module — called by app.py on every POST /events/report.

Loads hotspot_index.json ONCE at startup (load_hotspot_index()),
then flags each incoming event with flag_hotspot() in microseconds.

Match priority:
  1. Exact junction match  (fastest, highest confidence)
  2. Exact address match   (high confidence)
  3. Fuzzy address match   (requires rapidfuzz, falls back to None if not installed)
  4. No match              → is_hotspot: False

Usage in app.py:
    from ml_models.hotspot_flag.src.flag import load_hotspot_index, flag_hotspot

    # At startup (once):
    hotspot_index = load_hotspot_index()

    # Per request:
    result = flag_hotspot(hotspot_index,
                          junction=event.junction,
                          address=event.address)
    # result["is_hotspot"] → True/False
    # result["tier"]       → "critical" / "high" / "moderate" / None
"""

import json
import os
from typing import Optional

INDEX_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "hotspot_index.json"
)


FUZZY_THRESHOLD = 85


try:
    from rapidfuzz import process as fuzz_process, fuzz

    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


def load_hotspot_index(path: str = INDEX_PATH) -> dict:
    """
    Load hotspot_index.json into memory.
    Call ONCE at server startup — not per request.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(
        f"[hotspot] Loaded index: "
        f"{data['total_junctions']} junctions, "
        f"{data['total_addresses']} addresses flagged as hotspots "
        f"(>={data['min_events']} events)."
    )
    return data


def _no_match_result(junction: Optional[str], address: Optional[str]) -> dict:
    return {
        "is_hotspot": False,
        "hotspot_tier": None,
        "historical_count": 0,
        "dominant_cause": None,
        "cause_breakdown": {},
        "avg_resolution_min": None,
        "route_to": "Traffic Police",
        "route_reason": "No hotspot history at this location. Standard dispatch.",
        "match_type": "none",
        "match_score": 0,
        "matched_name": None,
    }


def flag_hotspot(
    index: dict,
    junction: Optional[str] = None,
    address: Optional[str] = None,
) -> dict:
    """
    Flag an incoming event as a known hotspot or not.

    Parameters
    ----------
    index    : output of load_hotspot_index()
    junction : junction field from the incoming event (may be None)
    address  : address field from the incoming event (may be None)

    Returns
    -------
    dict — see README for full schema
    """
    junction_index = index["junction_index"]
    address_index = index["address_index"]

    if junction and junction in junction_index:
        data = junction_index[junction]
        return {
            "is_hotspot": True,
            "hotspot_tier": data["tier"],
            "historical_count": data["total_events"],
            "dominant_cause": data["dominant_cause"],
            "cause_breakdown": data["cause_breakdown"],
            "avg_resolution_min": data["avg_resolution_min"],
            "route_to": data["route_to"],
            "route_reason": data["route_reason"],
            "match_type": "junction",
            "match_score": 100,
            "matched_name": junction,
            "lat": data.get("lat"),
            "lng": data.get("lng"),
        }

    if address and address in address_index:
        data = address_index[address]
        return {
            "is_hotspot": True,
            "hotspot_tier": data["tier"],
            "historical_count": data["total_events"],
            "dominant_cause": data["dominant_cause"],
            "cause_breakdown": data["cause_breakdown"],
            "avg_resolution_min": data["avg_resolution_min"],
            "route_to": data["route_to"],
            "route_reason": data["route_reason"],
            "match_type": "address_exact",
            "match_score": 100,
            "matched_name": address,
            "lat": data.get("lat"),
            "lng": data.get("lng"),
        }

    if address and FUZZY_AVAILABLE and address_index:
        known_addresses = list(address_index.keys())
        match_result = fuzz_process.extractOne(
            address,
            known_addresses,
            scorer=fuzz.token_sort_ratio,
        )
        if match_result and match_result[1] >= FUZZY_THRESHOLD:
            matched_addr = match_result[0]
            score = match_result[1]
            data = address_index[matched_addr]
            return {
                "is_hotspot": True,
                "hotspot_tier": data["tier"],
                "historical_count": data["total_events"],
                "dominant_cause": data["dominant_cause"],
                "cause_breakdown": data["cause_breakdown"],
                "avg_resolution_min": data["avg_resolution_min"],
                "route_to": data["route_to"],
                "route_reason": data["route_reason"],
                "match_type": "address_fuzzy",
                "match_score": score,
                "matched_name": matched_addr,
                "lat": data.get("lat"),
                "lng": data.get("lng"),
            }

    return _no_match_result(junction, address)


if __name__ == "__main__":
    print("[flag] Loading hotspot index for smoke test...")
    idx = load_hotspot_index()

    test_cases = [
        ("MekhriCircle", None, "Known junction hotspot - expect critical/high match"),
        ("SilkBoardJunc", None, "Known junction hotspot - expect match"),
        (
            None,
            "Outer Ring Road, Karthik Nagar, Marathahalli, Bengaluru, Karnataka. Pin-560037 (India)",
            "Exact address match - top hotspot (88 events)",
        ),
        (
            None,
            "Outer Ring Road, Marathahalli, Bengaluru",
            "Partial/fuzzy address - may match with rapidfuzz",
        ),
        ("UnknownJunction", None, "Unknown junction - expect no match"),
        (None, None, "Neither field provided - expect no match"),
    ]

    print()
    for junc, addr, desc in test_cases:
        result = flag_hotspot(idx, junction=junc, address=addr)
        print(f"  -- {desc}")
        print(
            f"     is_hotspot={result['is_hotspot']}  "
            f"tier={result['hotspot_tier']}  "
            f"count={result['historical_count']}  "
            f"match={result['match_type']}  "
            f"route->{result['route_to']}"
        )
        if result["is_hotspot"]:
            print(f"     {result['route_reason']}")
        print()

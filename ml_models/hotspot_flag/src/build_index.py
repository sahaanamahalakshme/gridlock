"""
build_index.py
--------------
ONE-TIME SETUP SCRIPT — run before starting the server.

Reads the raw ASTRAM CSV and builds two hotspot indexes:
  1. Junction-level index (85 junctions with 10+ events)
  2. Address-level index (138 addresses with 10+ events)

For each hotspot location, pre-computes:
  - total event count
  - tier (critical / high / moderate)
  - dominant cause
  - top 3 causes with counts
  - average resolution time (minutes)
  - routing recommendation (Traffic Police / BBMP / BWSSB)

Output: output/hotspot_index.json

Run:
    cd gridlock/ml_models/hotspot_flag
    python src/build_index.py
"""

import pandas as pd
import numpy as np
import json
import os

RAW_CSV = os.path.join("data", "astram_raw.csv")
OUT_PATH = os.path.join("output", "hotspot_index.json")


MIN_EVENTS = 10


TIERS = {
    "critical": 50,
    "high": 25,
    "moderate": 10,
}


ROUTE_MAP = {
    "pot_holes": ("BBMP", "pothole/road-surface damage is BBMP jurisdiction"),
    "road_conditions": ("BBMP", "road condition issue is BBMP jurisdiction"),
    "construction": ("BBMP", "construction-related disruption - coordinate with BBMP"),
    "water_logging": ("BWSSB", "water logging is BWSSB jurisdiction"),
    "Debris": ("BBMP", "debris clearance is BBMP responsibility"),
    "debris": ("BBMP", "debris clearance is BBMP responsibility"),
    "tree_fall": ("BBMP", "tree clearance - BBMP crew required"),
}


def load_and_parse(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["start"] = pd.to_datetime(df["start_datetime"], utc=True, errors="coerce")
    df["resolved"] = pd.to_datetime(df["resolved_datetime"], utc=True, errors="coerce")
    df["closed"] = pd.to_datetime(df["closed_datetime"], utc=True, errors="coerce")
    df["end_time"] = df["resolved"].fillna(df["closed"])
    df["duration_min"] = (df["end_time"] - df["start"]).dt.total_seconds() / 60

    df.loc[df["duration_min"] < 0, "duration_min"] = np.nan
    df.loc[df["duration_min"] > 600, "duration_min"] = np.nan
    print(f"[hotspot] Loaded {len(df)} rows")
    return df


def _tier(count: int) -> str:
    if count >= TIERS["critical"]:
        return "critical"
    if count >= TIERS["high"]:
        return "high"
    return "moderate"


def _route(cause_breakdown: dict, total: int) -> tuple[str, str]:
    """Return (department, reason) based on dominant cause."""
    if not cause_breakdown:
        return "Traffic Police", "insufficient cause data - default dispatch"
    top_cause = max(cause_breakdown, key=cause_breakdown.get)
    top_frac = cause_breakdown[top_cause] / total
    if top_frac > 0.40 and top_cause in ROUTE_MAP:
        dept, reason = ROUTE_MAP[top_cause]
        return (
            dept,
            f"{top_cause} is the dominant cause ({top_frac:.0%} of events). {reason}.",
        )
    return (
        "Traffic Police",
        f"{top_cause} is the dominant cause ({top_frac:.0%} of events). Standard traffic dispatch applies.",
    )


def build_junction_index(df: pd.DataFrame) -> dict:
    valid = df.dropna(subset=["junction"])
    counts = valid["junction"].value_counts()
    hotspot_junctions = counts[counts >= MIN_EVENTS].index.tolist()

    index = {}
    for junc in hotspot_junctions:
        subset = valid[valid["junction"] == junc]
        cause_counts = subset["event_cause"].value_counts().head(3).to_dict()
        cause_counts = {str(k): int(v) for k, v in cause_counts.items()}
        avg_dur = subset["duration_min"].mean()
        total = len(subset)
        route_to, route_reason = _route(cause_counts, total)

        index[junc] = {
            "total_events": total,
            "tier": _tier(total),
            "dominant_cause": (
                max(cause_counts, key=cause_counts.get) if cause_counts else "unknown"
            ),
            "cause_breakdown": cause_counts,
            "avg_resolution_min": (
                round(float(avg_dur), 1) if not np.isnan(avg_dur) else None
            ),
            "route_to": route_to,
            "route_reason": route_reason,
            "lat": round(float(subset["latitude"].mean()), 6),
            "lng": round(float(subset["longitude"].mean()), 6),
        }

    print(f"[hotspot] Junction index: {len(index)} hotspot junctions")
    return index


def build_address_index(df: pd.DataFrame) -> dict:
    valid = df.dropna(subset=["address"])
    counts = valid["address"].value_counts()
    hotspot_addresses = counts[counts >= MIN_EVENTS].index.tolist()

    index = {}
    for addr in hotspot_addresses:
        subset = valid[valid["address"] == addr]
        cause_counts = subset["event_cause"].value_counts().head(3).to_dict()
        cause_counts = {str(k): int(v) for k, v in cause_counts.items()}
        avg_dur = subset["duration_min"].mean()
        total = len(subset)
        route_to, route_reason = _route(cause_counts, total)

        index[addr] = {
            "total_events": total,
            "tier": _tier(total),
            "dominant_cause": (
                max(cause_counts, key=cause_counts.get) if cause_counts else "unknown"
            ),
            "cause_breakdown": cause_counts,
            "avg_resolution_min": (
                round(float(avg_dur), 1) if not np.isnan(avg_dur) else None
            ),
            "route_to": route_to,
            "route_reason": route_reason,
            "lat": round(float(subset["latitude"].mean()), 6),
            "lng": round(float(subset["longitude"].mean()), 6),
        }

    print(f"[hotspot] Address index: {len(index)} hotspot addresses")
    return index


def print_summary(junction_index: dict, address_index: dict) -> None:

    top5_j = sorted(
        junction_index.items(), key=lambda x: x[1]["total_events"], reverse=True
    )[:5]
    print("\n[hotspot] Top 5 junction hotspots:")
    for name, data in top5_j:
        print(
            f"  {name}: {data['total_events']} events | "
            f"tier={data['tier']} | dominant={data['dominant_cause']} | "
            f"→ {data['route_to']}"
        )

    top5_a = sorted(
        address_index.items(), key=lambda x: x[1]["total_events"], reverse=True
    )[:5]
    print("\n[hotspot] Top 5 address hotspots:")
    for addr, data in top5_a:
        short_addr = addr[:60] + "..." if len(addr) > 60 else addr
        print(f"  {short_addr}: {data['total_events']} events | tier={data['tier']}")

    from collections import Counter

    j_tiers = Counter(d["tier"] for d in junction_index.values())
    a_tiers = Counter(d["tier"] for d in address_index.values())
    print(f"\n[hotspot] Junction tiers: {dict(j_tiers)}")
    print(f"[hotspot] Address tiers:  {dict(a_tiers)}")


def save(junction_index: dict, address_index: dict, path: str) -> None:
    out = {
        "min_events": MIN_EVENTS,
        "tiers": TIERS,
        "junction_index": junction_index,
        "address_index": address_index,
        "total_junctions": len(junction_index),
        "total_addresses": len(address_index),
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(path) / 1024
    print(f"\n[hotspot] Saved → {path}  ({size_kb:.1f} KB)")


def main():
    df = load_and_parse(RAW_CSV)
    junction_index = build_junction_index(df)
    address_index = build_address_index(df)
    print_summary(junction_index, address_index)
    save(junction_index, address_index, OUT_PATH)
    print("\n[hotspot] Done. Run src/flag.py to verify.")


if __name__ == "__main__":
    main()

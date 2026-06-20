"""
corridor_cache.py
==================
Person A — STEP A1

Run this ONCE, before the hackathon demo. Not called live by the API.

WHAT IT DOES:
    Takes the 21 corridor names that ACTUALLY APPEAR in your dataset's
    `corridor` column (extracted by analyzing astram_events_raw.csv — not
    guessed, not hand-typed) and fetches each one's real road geometry
    from OpenStreetMap (Nominatim for search, Overpass for the actual
    line-shape of the road), then saves everything to:

        diversion_engine/data/corridors.json

WHY these specific 21 names:
    They come directly from value_counts() on your `corridor` column —
    every name here was actually used by a real officer logging a real
    event. "Non-corridor" (3,124 rows) is excluded on purpose — it means
    "this event wasn't on a tracked corridor," not a road name, so it
    can't be diverted to/from.

OUTPUT SHAPE (corridors.json):
{
  "Mysore Road": {
    "osm_query": "Mysore Road, Bengaluru, India",
    "points": [[12.95, 77.55], [12.96, 77.54], ...],   # real road polyline
    "centroid": [12.955, 77.545],
    "n_historical_events": 743,                        # from your CSV, for reference
    "matched": true
  },
  ...
  "CBD 2": {
    "osm_query": "...",
    "points": [],
    "centroid": null,
    "n_historical_events": 104,
    "matched": false,          # OSM couldn't resolve this one — see note below
    "note": "No OSM match — needs manual fallback centroid (see FALLBACK_CENTROIDS)."
  }
}

A FEW NAMES WON'T RESOLVE CLEANLY ON OSM — and that's expected, not a bug:
    Names like "ORR East 1", "ORR West 1", "CBD 1/2", "Bellary Road 1/2"
    are YOUR project's segment labels for stretches of bigger real roads
    (Outer Ring Road, Bellary Road, the Central Business District area) —
    OSM doesn't know these segment names. For those, the script falls
    back to a centroid computed directly from YOUR OWN dataset's
    lat/long points for that corridor label (see compute_fallback_from_data()).
    This is more honest than pretending OSM has a segment it doesn't.

USAGE:
    python src/corridor_cache.py --raw-csv /path/to/astram_events_raw.csv

    (Defaults to data/raw/astram_events_raw.csv relative to project root
    if --raw-csv is not given — same convention as clean_data.py.)
"""

import sys
import json
import time
import argparse
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT        = Path(__file__).resolve().parent.parent
DEFAULT_RAW = ROOT.parent / "data" / "raw" / "astram_events_raw.csv"
OUTPUT_JSON = ROOT / "data" / "corridors.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"

# Required by Nominatim/Overpass usage policy — identify yourself honestly.
HEADERS = {"User-Agent": "gridlock-hackathon-corridor-cache/1.0 (educational project)"}

REQUEST_DELAY_SEC = 1.1   # Nominatim/Overpass both throttle ~1 req/sec — respect it


def http_get_json(url: str, params: dict) -> list | dict:
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def nominatim_search(query: str) -> dict | None:
    """Find the OSM way/relation ID for a road name near Bengaluru."""
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "in",
        "viewbox": "77.40,13.18,77.85,12.75",  # rough Bengaluru bounding box
        "bounded": 1,
    }
    results = http_get_json(NOMINATIM_URL, params)
    if not results:
        return None
    return results[0]


def overpass_way_geometry(osm_type: str, osm_id: str) -> list[list[float]]:
    """
    Fetch the actual line geometry for a way/relation from Overpass.
    Returns a list of [lat, lng] points tracing the road.
    """
    if osm_type == "way":
        ql = f"""
        [out:json][timeout:25];
        way({osm_id});
        out geom;
        """
    elif osm_type == "relation":
        ql = f"""
        [out:json][timeout:25];
        relation({osm_id});
        way(r);
        out geom;
        """
    else:
        return []

    req = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": ql}).encode(),
        headers=HEADERS,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    Overpass error: {e}")
        return []

    points = []
    for element in data.get("elements", []):
        geometry = element.get("geometry", [])
        for pt in geometry:
            points.append([pt["lat"], pt["lon"]])
    return points


def compute_fallback_from_data(df: pd.DataFrame, corridor_name: str) -> dict:
    """
    Build geometry from YOUR OWN dataset when OSM can't resolve a name.
    Uses every event's lat/lng tagged with this corridor as a point cloud —
    not as clean as a real road polyline, but it's real, honest data from
    your own 8,173 rows, not an invented shape.
    """
    sub = df[df["corridor"] == corridor_name]
    sub = sub.dropna(subset=["latitude", "longitude"])
    sub = sub[(sub["latitude"] != 0) & (sub["longitude"] != 0)]
    if len(sub) == 0:
        return {"points": [], "centroid": None}

    points = sub[["latitude", "longitude"]].values.tolist()
    centroid = [sub["latitude"].mean(), sub["longitude"].mean()]
    return {"points": points, "centroid": centroid}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-csv", type=str, default=str(DEFAULT_RAW))
    args = parser.parse_args()

    raw_csv = Path(args.raw_csv)
    print(f"[corridor_cache] Reading raw CSV: {raw_csv}")
    if not raw_csv.exists():
        print(f"ERROR: raw CSV not found at {raw_csv}")
        sys.exit(1)

    df = pd.read_csv(raw_csv, low_memory=False)

    # ── Step 1: extract the real corridor list from the data ──────────────────
    corridor_counts = df["corridor"].value_counts()
    corridor_counts = corridor_counts.drop("Non-corridor", errors="ignore")
    corridor_names = corridor_counts.index.tolist()

    print(f"\n[corridor_cache] Found {len(corridor_names)} real corridor names in the dataset:")
    for name in corridor_names:
        print(f"  {name:25s}  ({corridor_counts[name]:,} historical events)")

    result = {}

    for name in corridor_names:
        print(f"\n[corridor_cache] Resolving: '{name}' ...")
        query = f"{name}, Bengaluru, India"

        osm_match = None
        try:
            osm_match = nominatim_search(query)
        except Exception as e:
            print(f"    Nominatim error: {e}")

        time.sleep(REQUEST_DELAY_SEC)

        points, centroid, matched, note = [], None, False, None

        if osm_match:
            osm_type = osm_match.get("osm_type")  # "way" or "relation"
            osm_id   = osm_match.get("osm_id")
            print(f"    OSM match: {osm_type} {osm_id} — '{osm_match.get('display_name', '')[:70]}'")
            points = overpass_way_geometry(osm_type, osm_id)
            time.sleep(REQUEST_DELAY_SEC)

            if points:
                lats = [p[0] for p in points]
                lngs = [p[1] for p in points]
                centroid = [sum(lats) / len(lats), sum(lngs) / len(lngs)]
                matched = True
                print(f"    Got {len(points)} geometry points.")
            else:
                note = "OSM matched a place but returned no line geometry — using data fallback."
        else:
            note = "No OSM match for this corridor segment name — using data fallback."

        if not matched:
            print(f"    {note}")
            fallback = compute_fallback_from_data(df, name)
            points = fallback["points"]
            centroid = fallback["centroid"]
            if points:
                print(f"    Fallback: {len(points)} points from your own dataset's lat/lng for this corridor.")

        result[name] = {
            "osm_query": query,
            "points": points,
            "centroid": centroid,
            "n_historical_events": int(corridor_counts[name]),
            "matched": matched,
            "note": note,
        }

    # ── Save ─────────────────────────────────────────────────────────────────
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[corridor_cache] === SUMMARY ===")
    matched_count = sum(1 for v in result.values() if v["matched"])
    print(f"  OSM-matched corridors : {matched_count} / {len(result)}")
    print(f"  Data-fallback corridors: {len(result) - matched_count} / {len(result)}")
    print(f"\n[corridor_cache] Saved -> {OUTPUT_JSON}")
    print("[corridor_cache] Commit this file to the repo. route_lookup.py reads it, doesn't fetch live.")


if __name__ == "__main__":
    main()
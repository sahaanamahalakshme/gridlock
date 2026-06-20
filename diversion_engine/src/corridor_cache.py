import sys
import json
import time
import argparse
import urllib.parse
import urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW = ROOT.parent / "data" / "raw" / "astram_events_raw.csv"
OUTPUT_JSON = ROOT / "data" / "corridors.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "gridlock-hackathon-corridor-cache/1.0 (educational project)"}
REQUEST_DELAY_SEC = 1.1


def http_get_json(url: str, params: dict) -> list | dict:
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def nominatim_search(query: str) -> dict | None:
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "in",
        "viewbox": "77.40,13.18,77.85,12.75",
        "bounded": 1,
    }
    results = http_get_json(NOMINATIM_URL, params)
    if not results:
        return None
    return results[0]


def overpass_way_geometry(osm_type: str, osm_id: str) -> list[list[float]]:
    if osm_type == "way":
        ql = f"\n        [out:json][timeout:25];\n        way({osm_id});\n        out geom;\n        "
    elif osm_type == "relation":
        ql = f"\n        [out:json][timeout:25];\n        relation({osm_id});\n        way(r);\n        out geom;\n        "
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
    corridor_counts = df["corridor"].value_counts()
    corridor_counts = corridor_counts.drop("Non-corridor", errors="ignore")
    corridor_names = corridor_counts.index.tolist()
    print(
        f"\n[corridor_cache] Found {len(corridor_names)} real corridor names in the dataset:"
    )
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
        points, centroid, matched, note = ([], None, False, None)
        if osm_match:
            osm_type = osm_match.get("osm_type")
            osm_id = osm_match.get("osm_id")
            print(
                f"    OSM match: {osm_type} {osm_id} — '{osm_match.get('display_name', '')[:70]}'"
            )
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
                print(
                    f"    Fallback: {len(points)} points from your own dataset's lat/lng for this corridor."
                )
        result[name] = {
            "osm_query": query,
            "points": points,
            "centroid": centroid,
            "n_historical_events": int(corridor_counts[name]),
            "matched": matched,
            "note": note,
        }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[corridor_cache] === SUMMARY ===")
    matched_count = sum((1 for v in result.values() if v["matched"]))
    print(f"  OSM-matched corridors : {matched_count} / {len(result)}")
    print(f"  Data-fallback corridors: {len(result) - matched_count} / {len(result)}")
    print(f"\n[corridor_cache] Saved -> {OUTPUT_JSON}")
    print(
        "[corridor_cache] Commit this file to the repo. route_lookup.py reads it, doesn't fetch live."
    )


if __name__ == "__main__":
    main()


import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
 
try:
    import requests
except ImportError:
    print("ERROR: this script needs the 'requests' library.")
    print("Run: pip install requests")
    sys.exit(1)
 
OUTPUT_PATH = Path(__file__).resolve().parent / "bangalore_road_cache.json"
 
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "gridlock-hackathon-road-cache/1.0 (educational project)"}
 
# Rough Bangalore bounding box (south, west, north, east)
# Slightly generous to cover outer areas like Whitefield, Electronic City,
# Yelahanka -- adjust if your demo area extends further.
BBOX = {
    "south": 12.83,
    "west": 77.44,
    "north": 13.14,
    "east": 77.78,
}
 
# Overpass times out / struggles on very large single queries. Chunking
# the city into a grid of smaller boxes keeps each request fast and
# reliable, even on the free instance.
GRID_ROWS = 3
GRID_COLS = 3
 
REQUEST_DELAY_SEC = 2.0  # be polite -- this is a one-time script, not a hot path
MAX_RETRIES = 3
 
 
def build_grid_cells():
    """Split the Bangalore bbox into GRID_ROWS x GRID_COLS smaller cells."""
    lat_step = (BBOX["north"] - BBOX["south"]) / GRID_ROWS
    lng_step = (BBOX["east"] - BBOX["west"]) / GRID_COLS
 
    cells = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            s = BBOX["south"] + r * lat_step
            n = BBOX["south"] + (r + 1) * lat_step
            w = BBOX["west"] + c * lng_step
            e = BBOX["west"] + (c + 1) * lng_step
            cells.append((s, w, n, e))
    return cells
 
 
def fetch_cell(south, west, north, east, cell_num, total_cells):
    query = f"""
    [out:json][timeout:60];
    way["highway"~"^(trunk|primary|secondary|tertiary)(|_link)$"]["name"]
       ({south},{west},{north},{east});
    out geom;
    """
 
    for attempt in range(MAX_RETRIES):
        print(f"  [cell {cell_num}/{total_cells}] attempt {attempt + 1}/{MAX_RETRIES} ...")
        try:
            resp = requests.post(
                OVERPASS_URL,
                data={"data": query},
                headers=HEADERS,
                timeout=90,
            )
        except requests.RequestException as e:
            print(f"    Network error: {e}")
            time.sleep(5 * (attempt + 1))
            continue
 
        if resp.status_code == 429:
            print("    Rate limited (429) -- waiting before retry...")
            time.sleep(10 * (attempt + 1))
            continue
        if resp.status_code == 504:
            print("    Gateway timeout (504) -- waiting before retry...")
            time.sleep(8 * (attempt + 1))
            continue
        if resp.status_code != 200:
            print(f"    Unexpected status {resp.status_code}: {resp.text[:200]}")
            time.sleep(5)
            continue
 
        try:
            data = resp.json()
        except ValueError:
            print("    Could not parse JSON response.")
            continue
 
        elements = data.get("elements", [])
        print(f"    Got {len(elements)} road segments.")
        return elements
 
    print(f"    GAVE UP on cell {cell_num} after {MAX_RETRIES} attempts.")
    return []
 
 
def main():
    cells = build_grid_cells()
    print(f"[build_road_cache] Fetching Bangalore major roads in {len(cells)} chunks...")
    print(f"[build_road_cache] Bounding box: {BBOX}")
 
    all_roads = {}  # keyed by (name, first-coord) to reduce exact duplicates across cells
 
    for i, (south, west, north, east) in enumerate(cells, 1):
        elements = fetch_cell(south, west, north, east, i, len(cells))
 
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")
            highway = tags.get("highway")
            geometry = el.get("geometry", [])
            if not name or not geometry:
                continue
 
            points = [[pt["lat"], pt["lon"]] for pt in geometry]
            # Dedup key: name + rounded first point, so the same physical
            # road segment appearing in two adjacent grid cells (common at
            # chunk boundaries) doesn't get stored twice.
            key = (name, round(points[0][0], 4), round(points[0][1], 4))
 
            if key not in all_roads:
                all_roads[key] = {
                    "name": name,
                    "highway": highway,
                    "geometry": points,
                }
 
        time.sleep(REQUEST_DELAY_SEC)
 
    roads_list = list(all_roads.values())
    print(f"\n[build_road_cache] Total unique road segments collected: {len(roads_list)}")
 
    output = {
        "roads": roads_list,
        "bbox": [BBOX["south"], BBOX["west"], BBOX["north"], BBOX["east"]],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
 
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"[build_road_cache] Saved -> {OUTPUT_PATH}  ({size_mb:.2f} MB)")
    print("[build_road_cache] Done. Commit this file to your frontend repo (e.g. frontend/public/)")
    print("[build_road_cache] rallyRouteAnalysis.js will check this cache BEFORE any live Overpass call.")
 
 
if __name__ == "__main__":
    main()
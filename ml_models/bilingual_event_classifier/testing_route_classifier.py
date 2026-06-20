import pandas as pd
from routing_map import route_event
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_PATH = SCRIPT_DIR / "../../memory/data/raw/astram_events_raw.csv"
EXPECTED_CIVIC_COUNT = 1645


def run():
    df = pd.read_csv(RAW_PATH, low_memory=False)

    routed = df["event_cause"].apply(route_event)
    df["routing_agency"] = routed.apply(lambda r: r["routing_agency"])
    df["is_ambiguous"] = routed.apply(lambda r: r["is_ambiguous"])

    breakdown = df["routing_agency"].value_counts()
    civic_count = breakdown.get("bbmp", 0) + breakdown.get("bwssb", 0)
    ambiguous_count = df["is_ambiguous"].sum()

    print("routing breakdown:")
    for agency, count in breakdown.items():
        print(f"  {agency:<10} {count:>5}  ({count/len(df):.1%})")
    print()
    print(
        f"civic (bbmp+bwssb) events: {civic_count}  (reference: {EXPECTED_CIVIC_COUNT})"
    )
    print(f"ambiguous (flagged, defaulted to police): {ambiguous_count}")
    print()
    print("ambiguous causes seen:")
    print(df[df["is_ambiguous"]]["event_cause"].value_counts())


if __name__ == "__main__":
    run()

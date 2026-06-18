"""
Run once, before anything else: loads the full 8173-row raw CSV into the
events table with source='historical'. This is what makes the memory store
non-empty on Day 1 - without it, day-1 retrieval has nothing to retrieve
and every confidence check would say "no_precedent" even for jurisdictions
that genuinely have hundreds of prior records.

Unlike clean_data.py in impact_forecaster (which narrows down to 444 planned
rows for one specific model), this keeps every event_type and every row with
a valid police_station/lat/long, since the memory store has to serve all
three models, not just retrieval.
"""
import pandas as pd
from db import init_db, SessionLocal
from models import Event

RAW_PATH = "data/raw/astram_events_raw.csv"

KEEP_COLS = [
    "id", "event_type", "event_cause", "status", "police_station", "corridor",
    "zone", "junction", "address", "latitude", "longitude", "priority",
    "requires_road_closure", "description", "start_datetime", "end_datetime",
    "closed_datetime", "resolved_datetime",
]


def _duration_minutes(row):
    end = row["resolved_datetime"] or row["closed_datetime"] or row["end_datetime"]
    start = row["start_datetime"]
    if pd.isna(end) or pd.isna(start):
        return None
    delta = (end - start).total_seconds() / 60
    return delta if delta >= 0 else None


def seed():
    df = pd.read_csv(RAW_PATH, low_memory=False)[KEEP_COLS]

    # rows with no police_station or no coordinates can't support the
    # confidence lookup or the map, and there are none in this dataset
    # (both are 0% null) - this filter is a safety net, not expected to drop rows
    df = df.dropna(subset=["police_station", "latitude", "longitude"])

    for col in ["start_datetime", "end_datetime", "closed_datetime", "resolved_datetime"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # start_datetime is NOT NULL in the schema - drop rows where it couldn't be parsed
    before = len(df)
    df = df.dropna(subset=["start_datetime"])
    dropped = before - len(df)
    if dropped:
        print(f"skipped {dropped} rows with unparseable start_datetime")



    init_db()
    session = SessionLocal()

    inserted = 0
    for _, row in df.iterrows():
        duration = _duration_minutes(row)
        event = Event(
            source_id=str(row["id"]),
            event_type=row["event_type"],
            event_cause=row["event_cause"],
            status=row["status"],
            source="historical",
            police_station=row["police_station"],
            corridor=row["corridor"] if pd.notna(row["corridor"]) else None,
            zone=row["zone"] if pd.notna(row["zone"]) else None,
            junction=row["junction"] if pd.notna(row["junction"]) else None,
            address=row["address"] if pd.notna(row["address"]) else None,
            latitude=row["latitude"],
            longitude=row["longitude"],
            priority=row["priority"] if pd.notna(row["priority"]) else None,
            requires_road_closure=bool(row["requires_road_closure"]),
            description=row["description"] if pd.notna(row["description"]) else None,
            start_datetime=row["start_datetime"] if pd.notna(row["start_datetime"]) else None,
            end_datetime=row["end_datetime"] if pd.notna(row["end_datetime"]) else None,
            closed_datetime=row["closed_datetime"] if pd.notna(row["closed_datetime"]) else None,
            resolved_datetime=row["resolved_datetime"] if pd.notna(row["resolved_datetime"]) else None,
            duration_minutes=duration,
        )
        session.add(event)
        inserted += 1

        # commit in batches of 500 to avoid sending one giant transaction
        if inserted % 500 == 0:
            session.commit()
            print(f"  committed {inserted} rows...")

    session.commit()
    session.close()
    print(f"seeded {inserted} historical events")


if __name__ == "__main__":
    seed()
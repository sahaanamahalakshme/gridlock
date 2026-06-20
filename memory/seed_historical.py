import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from memory.db import init_db, SessionLocal
from memory.models import Event

RAW_PATH = "data/raw/astram_events_raw.csv"

KEEP_COLS = [
    "id",
    "event_type",
    "event_cause",
    "status",
    "police_station",
    "corridor",
    "zone",
    "junction",
    "address",
    "latitude",
    "longitude",
    "priority",
    "requires_road_closure",
    "description",
    "start_datetime",
    "end_datetime",
    "closed_datetime",
    "resolved_datetime",
    "created_date",
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

    df = df.dropna(subset=["police_station", "latitude", "longitude"])

    for col in [
        "start_datetime",
        "end_datetime",
        "closed_datetime",
        "resolved_datetime",
        "created_date",
    ]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["start_datetime"] = df["start_datetime"].fillna(df["created_date"])
    before = len(df)
    df = df.dropna(subset=["start_datetime"]).copy()
    dropped = before - len(df)

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
            start_datetime=row["start_datetime"],
            end_datetime=row["end_datetime"] if pd.notna(row["end_datetime"]) else None,
            closed_datetime=(
                row["closed_datetime"] if pd.notna(row["closed_datetime"]) else None
            ),
            resolved_datetime=(
                row["resolved_datetime"] if pd.notna(row["resolved_datetime"]) else None
            ),
            duration_minutes=duration,
        )
        session.add(event)
        inserted += 1

    session.commit()
    session.close()
    print(f"dropped {dropped} rows with no usable start_datetime")
    print(f"seeded {inserted} historical events")


if __name__ == "__main__":
    seed()

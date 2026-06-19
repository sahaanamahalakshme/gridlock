"""Script to seed planned events into the database."""

import os

import sys

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd

from memory.db import SessionLocal

from memory.models import Event

RAW_PATH = Path(__file__).parent / "data/raw/astram_events_raw.csv"

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
]


def _duration_minutes(row):

    for col in ["resolved_datetime", "closed_datetime", "end_datetime"]:

        if pd.notna(row[col]):

            if pd.isna(row["start_datetime"]):

                return None

            delta = (row[col] - row["start_datetime"]).total_seconds() / 60

            return delta if delta >= 0 else None

    return None


def patch():

    df = pd.read_csv(RAW_PATH, low_memory=False)[KEEP_COLS]

    df = df[df["event_type"] == "planned"].copy()

    print(f"Total planned rows in CSV: {len (df )}")

    for col in [
        "start_datetime",
        "end_datetime",
        "closed_datetime",
        "resolved_datetime",
    ]:

        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    before = len(df)

    df = df.dropna(subset=["start_datetime", "latitude", "longitude", "police_station"])

    dropped = before - len(df)

    print(f"Rows with parseable start_datetime: {len (df )} (dropped {dropped })")

    session = SessionLocal()

    existing_ids = set(
        (
            row[0]
            for row in session.query(Event.source_id)
            .filter(Event.event_type == "planned")
            .all()
            if row[0] is not None
        )
    )

    print(f"Already in DB (planned): {len (existing_ids )}")

    inserted = 0

    skipped = 0

    failed = 0

    for _, row in df.iterrows():

        source_id = str(row["id"])

        if source_id in existing_ids:

            skipped += 1

            continue

        try:

            duration = _duration_minutes(row)

            def strip_tz(ts):

                if pd.isna(ts):

                    return None

                if hasattr(ts, "tzinfo") and ts.tzinfo is not None:

                    return ts.replace(tzinfo=None)

                return ts

            event = Event(
                source_id=source_id,
                event_type=row["event_type"],
                event_cause=row["event_cause"],
                status=row["status"],
                source="historical",
                police_station=row["police_station"],
                corridor=row["corridor"] if pd.notna(row["corridor"]) else None,
                zone=row["zone"] if pd.notna(row["zone"]) else None,
                junction=row["junction"] if pd.notna(row["junction"]) else None,
                address=row["address"] if pd.notna(row["address"]) else None,
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                priority=row["priority"] if pd.notna(row["priority"]) else None,
                requires_road_closure=bool(row["requires_road_closure"]),
                description=(
                    row["description"] if pd.notna(row["description"]) else None
                ),
                start_datetime=strip_tz(row["start_datetime"]),
                end_datetime=strip_tz(row["end_datetime"]),
                closed_datetime=strip_tz(row["closed_datetime"]),
                resolved_datetime=strip_tz(row["resolved_datetime"]),
                duration_minutes=duration,
            )

            session.add(event)

            session.commit()

            inserted += 1

        except Exception as e:

            session.rollback()

            failed += 1

            print(f"  FAILED row {source_id }: {e }")

    session.close()

    print()

    print(
        f"Done. inserted={inserted }  skipped(already in DB)={skipped }  failed={failed }"
    )

    print()

    if inserted > 0:

        print("Re-test /events/similar with:")

        print("  police_station=Cubbon Park  event_cause=public_event  corridor=CBD 2")

        print("Expected: confidence_tier='thin' or 'moderate', matches > 0")


if __name__ == "__main__":

    patch()

import pandas as pd


RAW_PATH = "data/raw/astram_events_raw.csv"

OUT_PATH = "data/processed/planned_events_clean.csv"


KEEP_COLS = [
    "id",
    "description",
    "event_cause",
    "corridor",
    "priority",
    "requires_road_closure",
    "address",
    "latitude",
    "longitude",
    "start_datetime",
    "end_datetime",
    "status",
]


def clean():

    df = pd.read_csv(RAW_PATH, low_memory=False)

    planned = df[df["event_type"] == "planned"].copy()

    planned = planned[KEEP_COLS]

    planned = planned[planned["description"].notna()].copy()

    for col in ["description", "event_cause", "corridor", "priority", "address"]:

        planned[col] = planned[col].astype(str).str.strip()

        planned.loc[planned[col].isin(["nan", "None", ""]), col] = pd.NA

    planned["start_datetime"] = pd.to_datetime(
        planned["start_datetime"], errors="coerce"
    )

    planned["end_datetime"] = pd.to_datetime(planned["end_datetime"], errors="coerce")

    duration = (
        planned["end_datetime"] - planned["start_datetime"]
    ).dt.total_seconds() / 60

    duration[duration < 0] = pd.NA

    planned["duration_minutes"] = duration

    planned["retrieval_text"] = (
        planned["event_cause"].fillna("unknown_cause")
        + " | "
        + planned["corridor"].fillna("unknown_corridor")
        + " | "
        + planned["description"]
    )

    planned = planned.reset_index(drop=True)

    planned.to_csv(OUT_PATH, index=False)

    print(f"input planned rows : 467")

    print(f"output clean rows  : {len (planned )}")

    print(
        f"rows with usable duration_minutes: {planned ['duration_minutes'].notna ().sum ()}"
    )

    return planned


if __name__ == "__main__":

    clean()

import pandas as pd
from sklearn.model_selection import train_test_split

IN_PATH = "data/processed/planned_events_clean.csv"
TRAIN_PATH = "data/splits/train.csv"
VAL_PATH = "data/splits/val.csv"
TEST_PATH = "data/splits/test.csv"

RANDOM_STATE = 42


def split():
    df = pd.read_csv(IN_PATH)

    counts = df["event_cause"].value_counts()
    rare = counts[counts < 6].index
    strat_col = df["event_cause"].where(~df["event_cause"].isin(rare), "others")

    train_df, rest_df = train_test_split(
        df, test_size=0.30, random_state=RANDOM_STATE, stratify=strat_col
    )
    rest_strat = strat_col.loc[rest_df.index]
    val_df, test_df = train_test_split(
        rest_df, test_size=0.50, random_state=RANDOM_STATE, stratify=rest_strat
    )

    train_df.to_csv(TRAIN_PATH, index=False)
    val_df.to_csv(VAL_PATH, index=False)
    test_df.to_csv(TEST_PATH, index=False)

    print(f"train: {len(train_df)}  val: {len(val_df)}  test: {len(test_df)}")


if __name__ == "__main__":
    split()
import sys

import hashlib

import numpy as np

import pandas as pd

from pathlib import Path

from collections import defaultdict


ROOT = Path(__file__).resolve().parent

CLEAN_CSV = ROOT / "data" / "processed" / "classifier_events_clean.csv"

SPLITS_DIR = ROOT / "data" / "splits"


TRAIN_RATIO = 0.70

VAL_RATIO = 0.15

TEST_RATIO = 0.15

RANDOM_SEED = 42


def text_group_id(text: str) -> str:

    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def group_stratified_split(df, label_col, group_col, train_r, val_r, seed):

    rng = np.random.default_rng(seed)

    group_label = df.groupby(group_col)[label_col].agg(lambda x: x.mode()[0]).to_dict()

    group_rows = defaultdict(list)

    for idx, row in df.iterrows():

        group_rows[row[group_col]].append(idx)

    labels = df[label_col].unique()

    train_idx, val_idx, test_idx = [], [], []

    for lbl in labels:

        lbl_groups = [g for g, l in group_label.items() if l == lbl]

        rng.shuffle(lbl_groups)

        total = sum(len(group_rows[g]) for g in lbl_groups)

        train_target = int(total * train_r)

        val_target = int(total * val_r)

        accumulated = 0

        for g in lbl_groups:

            idxs = group_rows[g]

            accumulated += len(idxs)

            if accumulated <= train_target:

                train_idx.extend(idxs)

            elif accumulated <= train_target + val_target:

                val_idx.extend(idxs)

            else:

                test_idx.extend(idxs)

    return (
        df.loc[train_idx].reset_index(drop=True),
        df.loc[val_idx].reset_index(drop=True),
        df.loc[test_idx].reset_index(drop=True),
    )


def main():

    print(f"[split_data] Reading: {CLEAN_CSV }")

    if not CLEAN_CSV.exists():

        print("ERROR: cleaned CSV not found. Run clean_data.py first.")

        sys.exit(1)

    df = pd.read_csv(CLEAN_CSV)

    print(f"[split_data] Loaded {len (df ):,} rows")

    df["_group"] = df["description"].apply(text_group_id)

    n_groups = df["_group"].nunique()

    print(
        f"[split_data] Unique description groups: {n_groups :,} (out of {len (df ):,} rows)"
    )

    train, val, test = group_stratified_split(
        df,
        label_col="event_cause",
        group_col="_group",
        train_r=TRAIN_RATIO,
        val_r=VAL_RATIO,
        seed=RANDOM_SEED,
    )

    for split_df in [train, val, test]:

        split_df.drop(columns=["_group"], inplace=True, errors="ignore")

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    train.to_csv(SPLITS_DIR / "train.csv", index=False)

    val.to_csv(SPLITS_DIR / "val.csv", index=False)

    test.to_csv(SPLITS_DIR / "test.csv", index=False)

    train_texts = set(train["description"].str.strip().str.lower())

    val_texts = set(val["description"].str.strip().str.lower())

    test_texts = set(test["description"].str.strip().str.lower())

    print(f"\n[split_data] Leakage check (target: 0 for all):")

    print(f"  train ∩ val  = {len (train_texts &val_texts )}")

    print(f"  train ∩ test = {len (train_texts &test_texts )}")

    print(f"  val   ∩ test = {len (val_texts &test_texts )}")

    print(f"\n[split_data] Split sizes:")

    print(f"  train : {len (train ):,}  ({100 *len (train )/len (df ):.1f}%)")

    print(f"  val   : {len (val ):,}    ({100 *len (val )/len (df ):.1f}%)")

    print(f"  test  : {len (test ):,}   ({100 *len (test )/len (df ):.1f}%)")

    print(f"\n[split_data] event_cause distribution in train:")

    print(train["event_cause"].value_counts().to_string())

    print(f"\n[split_data] Saved splits -> {SPLITS_DIR }")


if __name__ == "__main__":

    main()

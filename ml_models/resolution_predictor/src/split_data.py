"""
split_data.py
-------------
data/processed/resolution_events_clean.csv  →  data/splits/{train,val,test}.csv

Split ratios:  70% train / 15% val / 15% test
Stratified on event_cause so each cause appears in every split.

Run:
    python src/split_data.py
"""

import pandas as pd
import os
from sklearn.model_selection import train_test_split

IN_PATH  = os.path.join("data", "processed", "resolution_events_clean.csv")
SPLIT_DIR = os.path.join("data", "splits")


def main():
    df = pd.read_csv(IN_PATH)
    print(f"[split] Loaded {len(df)} rows from {IN_PATH}")

    # ── stratify on event_cause ──────────────────────────────────────────────
    # Some causes have very few examples (e.g. protest=2). If a stratum is
    # smaller than the number of splits sklearn will error, so we only
    # stratify when it's safe.
    cause_counts = df["event_cause"].value_counts()
    # A cause needs at least 3 members to survive two consecutive stratified splits
    rare_causes = cause_counts[cause_counts < 10].index.tolist()
    if rare_causes:
        print(f"[split] Rare causes (< 10 rows) bucketed as '__rare__' for stratification: {rare_causes}")

    def stratify_label(x):
        return "__rare__" if x in rare_causes else x

    stratify_col = df["event_cause"].apply(stratify_label)

    # 70% train, 30% temp
    train_df, temp_df = train_test_split(
        df, test_size=0.30, random_state=42, stratify=stratify_col
    )

    # Split temp 50/50 → 15% val, 15% test
    # Only stratify if every bucket has >= 2 members in temp
    temp_strat = temp_df["event_cause"].apply(stratify_label)
    temp_counts = temp_strat.value_counts()
    if temp_counts.min() >= 2:
        val_df, test_df = train_test_split(
            temp_df, test_size=0.50, random_state=42, stratify=temp_strat
        )
    else:
        print("[split] Temp split too small to stratify — splitting without stratification")
        val_df, test_df = train_test_split(
            temp_df, test_size=0.50, random_state=42
        )

    os.makedirs(SPLIT_DIR, exist_ok=True)
    train_df.to_csv(os.path.join(SPLIT_DIR, "train.csv"), index=False)
    val_df.to_csv(os.path.join(SPLIT_DIR, "val.csv"),   index=False)
    test_df.to_csv(os.path.join(SPLIT_DIR, "test.csv"), index=False)

    print(f"[split] train : {len(train_df)} rows  ({len(train_df)/len(df)*100:.1f}%)")
    print(f"[split] val   : {len(val_df)} rows  ({len(val_df)/len(df)*100:.1f}%)")
    print(f"[split] test  : {len(test_df)} rows  ({len(test_df)/len(df)*100:.1f}%)")
    print(f"\n[split] Saved splits to {SPLIT_DIR}/")
    print("[split] Done. Run src/train_model.py next.")


if __name__ == "__main__":
    main()
pip install -r requirements.txt

python src/clean_data.py       # raw 8173 rows -> 444 clean planned-event rows
python src/split_data.py       # 444 -> train 310 / val 67 / test 67
python src/build_index.py      # embeds train.csv, builds the NearestNeighbors index
python src/validate_tune.py    # tries k=1,3,5 on val.csv, prints metrics for each
# pick the best k from that output, set BEST_K in evaluate_test.py
python src/evaluate_test.py    # final, one-time number on test.csv
```

`src/retrieve.py` is what Person B's API calls at runtime - it's not part of
the offline pipeline above, it just loads the saved index and answers one
query at a time.

## What "before training" actually meant here, checked against your file

Out of the 467 rows where `event_type == 'planned'`:
- 23 have no `description` -> dropped, since there's nothing to embed.
- `resolved_datetime` is empty on all 467 of them, and `closed_datetime` is
  only filled on 33. Neither is usable as the primary outcome field for this
  subset.
- The only outcome signal that exists at any real scale is
  `end_datetime - start_datetime`, and even that is only valid (non-negative,
  both timestamps present) on 88 of the 467 rows. 3 rows have end before
  start (data entry errors) and were set to unknown rather than dropped,
  since the row is still useful for cause/corridor matching even without a
  duration.

Practical effect: your retrieval index will return a same-cause,
same-corridor precedent for almost every query, but it will only be able to
attach a "this took X minutes last time" outcome to roughly 1 in 5 of those
matches. Say that number out loud to judges rather than letting it surface
as a surprise - it's a property of the data, not a bug in the pipeline.

## Why no separate "training" step

Nearest-neighbor retrieval doesn't fit gradient-trained weights, so there's
no analogue to `model.fit(X, y)` here. The three-phase split still earns its
keep though: train.csv is the pool you search, val.csv is where you pick k
and could compare embedding-text templates, and test.csv is touched exactly
once, in evaluate_test.py, for the number you actually report.

import sys

import subprocess

import argparse

from pathlib import Path


HERE = Path(__file__).resolve().parent


STEPS = [
    ("clean", HERE / "clean_data.py", "Clean & normalise raw ASTRAM CSV"),
    ("split", HERE / "split_data.py", "Group-aware train/val/test split"),
    ("train", HERE / "train_model.py", "Embed (GPU) + train LR classifiers"),
    ("validate", HERE / "validate_tune.py", "Hyper-param sweep on val set"),
    ("evaluate", HERE / "evaluate_test.py", "Final evaluation on held-out test set"),
]


STEP_NAMES = [s[0] for s in STEPS]


def main():

    parser = argparse.ArgumentParser(
        description="Bilingual Event Classifier — full pipeline runner"
    )

    parser.add_argument(
        "--from",
        dest="start_from",
        default="clean",
        choices=STEP_NAMES,
        help="Start from this step (inclusive). Default: clean (full pipeline).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print steps that would run without executing them.",
    )

    args = parser.parse_args()

    start_idx = STEP_NAMES.index(args.start_from)

    steps_to_run = STEPS[start_idx:]

    print("\n" + "=" * 65)

    print("  BILINGUAL EVENT CLASSIFIER — TRAINING PIPELINE")

    print("=" * 65)

    print(f"  Starting from : {args .start_from }")

    print(f"  Steps to run  : {[s [0 ]for s in steps_to_run ]}")

    if args.dry_run:

        print("  Mode          : DRY RUN (nothing will execute)")

    print("=" * 65 + "\n")

    for i, (name, script, description) in enumerate(steps_to_run, 1):

        print(f"[{i }/{len (steps_to_run )}] {name .upper ():10}  {description }")

        if args.dry_run:

            print(f"         -> would run: python {script .name }\n")

            continue

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(HERE),
        )

        if result.returncode != 0:

            print(
                f"\n[pipeline] ERROR: step '{name }' failed (exit code {result .returncode })."
            )

            print("           Fix the error above and re-run with:")

            print(f"           python run_pipeline.py --from {name }")

            sys.exit(result.returncode)

        print(f"         ✓ {name } complete\n")

    print("=" * 65)

    print("  Pipeline finished successfully!")

    print("  Reports  ->  reports/test_report.txt")

    print("  Models   ->  models/cause_classifier.joblib")

    print("             models/priority_classifier.joblib")

    print("\n  To test inference:")

    print("  python predict.py")

    print("=" * 65 + "\n")


if __name__ == "__main__":

    main()

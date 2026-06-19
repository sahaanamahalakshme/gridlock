"""Integration tests for the complete pipeline."""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import json
import argparse
import importlib.util
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
CLASSIFIER_DIR = ROOT / "ml_models" / "bilingual_event_classifier"
RESOLUTION_DIR = ROOT / "ml_models" / "resolution_predictor"
FORECASTER_DIR = ROOT / "ml_models" / "impact_forecaster"


def import_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_all_models():
    print("\n" + "=" * 60)
    print("LOADING MODELS")
    print("=" * 60)
    print("\n[1/3] Loading bilingual_event_classifier ...")
    classifier_mod = import_module_from_path(
        "predict_classifier", CLASSIFIER_DIR / "predict.py"
    )
    print("\n[2/3] Loading resolution_predictor ...")
    resolution_mod = import_module_from_path(
        "predict_resolution", RESOLUTION_DIR / "src" / "predict.py"
    )
    resolution_artifacts = resolution_mod.load_artifacts(
        model_dir=str(RESOLUTION_DIR / "models")
    )
    print("\n[3/3] Loading impact_forecaster ...")
    forecaster_mod = import_module_from_path(
        "retrieve", FORECASTER_DIR / "src" / "retrieve.py"
    )
    forecaster_mod.load_artifacts()
    print("\n✓ All models loaded.\n")
    return (classifier_mod, resolution_mod, resolution_artifacts, forecaster_mod)


def run_pipeline(
    description: str,
    corridor: str,
    police_station: str,
    requires_road_closure: bool,
    hour_of_day: int,
    day_of_week: int,
    classifier_mod,
    resolution_mod,
    resolution_artifacts,
    forecaster_mod,
) -> dict:
    print("  → Running classifier ...")
    clf_result = classifier_mod.classify(description)
    predicted_cause = clf_result["event_cause"]
    cause_confidence = clf_result["cause_confidence"]
    severity = clf_result["severity"]
    severity_conf = clf_result["severity_confidence"]
    top3_causes = clf_result["top3_causes"]
    print("  → Running resolution predictor ...")
    res_result = resolution_mod.predict(
        resolution_artifacts,
        {
            "event_cause": predicted_cause,
            "corridor": corridor,
            "priority": severity,
            "requires_road_closure": requires_road_closure,
            "police_station": police_station,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
        },
    )
    predicted_minutes = res_result["predicted_minutes"]
    confidence_band = res_result["confidence_band"]
    print("  → Running impact forecaster ...")
    similar_events = forecaster_mod.retrieve_similar_event(
        event_cause=predicted_cause, corridor=corridor, description=description, k=3
    )
    return {
        "input": {
            "description": description,
            "corridor": corridor,
            "police_station": police_station,
            "requires_road_closure": requires_road_closure,
        },
        "classification": {
            "event_cause": predicted_cause,
            "cause_confidence_pct": round(cause_confidence * 100, 1),
            "severity": severity,
            "severity_confidence_pct": round(severity_conf * 100, 1),
            "top3_causes": top3_causes,
        },
        "resolution": {
            "predicted_minutes": predicted_minutes,
            "predicted_hours_mins": f"{int(predicted_minutes // 60)}h {int(predicted_minutes % 60)}m",
            "confidence_band_mins": confidence_band,
        },
        "similar_past_events": similar_events,
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
        },
    }


def pretty_print(result: dict):
    print("\n" + "=" * 60)
    print("PIPELINE OUTPUT")
    print("=" * 60)
    inp = result["input"]
    print(f"\n📥 INPUT")
    print(f"   Description       : {inp['description']}")
    print(f"   Corridor          : {inp['corridor']}")
    print(f"   Police Station    : {inp['police_station']}")
    print(f"   Road Closure      : {inp['requires_road_closure']}")
    clf = result["classification"]
    print(f"\n🏷️  CLASSIFICATION  (bilingual_event_classifier)")
    print(
        f"   Event Cause       : {clf['event_cause']}  ({clf['cause_confidence_pct']}% confidence)"
    )
    print(
        f"   Severity          : {clf['severity']}  ({clf['severity_confidence_pct']}% confidence)"
    )
    print(f"   Top-3 Causes      :")
    for t in clf["top3_causes"]:
        bar = "█" * int(t["confidence"] * 20)
        print(f"      {t['label']:<25} {t['confidence'] * 100:5.1f}%  {bar}")
    res = result["resolution"]
    print(f"\n⏱️  RESOLUTION TIME  (resolution_predictor)")
    print(
        f"   Predicted         : {res['predicted_minutes']} min  ({res['predicted_hours_mins']})"
    )
    print(
        f"   Confidence Band   : {res['confidence_band_mins'][0]} – {res['confidence_band_mins'][1]} min"
    )
    sim = result["similar_past_events"]
    print(f"\n🔍 SIMILAR PAST EVENTS  (impact_forecaster)")
    if sim:
        for i, s in enumerate(sim, 1):
            dur = (
                f"{s['known_duration_minutes']} min"
                if s.get("known_duration_minutes")
                else "N/A"
            )
            print(
                f"   [{i}] {s['event_cause']:<22} | Corridor: {s.get('corridor', '?'):<15} | Duration: {dur:<10} | Similarity: {s['similarity']}"
            )
            print(f"        Description: {str(s.get('description', ''))[:80]}")
    else:
        print("   No similar events found.")
    print(f"\n🕐 Meta: {result['meta']['timestamp']}")
    print("=" * 60 + "\n")


TEST_CASES = [
    {
        "description": "Vehicle breakdown on Mysore road near toll gate, heavy traffic",
        "corridor": "Mysore Road",
        "police_station": "Kengeri",
        "requires_road_closure": False,
        "hour_of_day": 8,
        "day_of_week": 1,
    },
    {
        "description": "ಬಿಎಂಟಿಸಿ ಬಸ್ ಕೆಟ್ಟು ನಿಂತಿದೆ ಸರ್",
        "corridor": "ORR East 1",
        "police_station": "HSR Layout",
        "requires_road_closure": False,
        "hour_of_day": 9,
        "day_of_week": 2,
    },
    {
        "description": "Road blocked due to fallen tree after storm",
        "corridor": "CBD 1",
        "police_station": "Cubbon Park",
        "requires_road_closure": True,
        "hour_of_day": 14,
        "day_of_week": 3,
    },
    {
        "description": "Cricket match at Chinnaswamy stadium, expect heavy footfall and traffic",
        "corridor": "CBD 2",
        "police_station": "Shivajinagar",
        "requires_road_closure": False,
        "hour_of_day": 18,
        "day_of_week": 6,
    },
    {
        "description": "Heavy waterlogging near underpass, vehicles stranded",
        "corridor": "Hebbal",
        "police_station": "Hebbal",
        "requires_road_closure": True,
        "hour_of_day": 17,
        "day_of_week": 4,
    },
]


def main():
    parser = argparse.ArgumentParser(
        description="Integration test for all 3 SENTRY models."
    )
    parser.add_argument(
        "--desc", type=str, default=None, help="Custom description text"
    )
    parser.add_argument(
        "--corridor", type=str, default="ORR East 1", help="Corridor name"
    )
    parser.add_argument(
        "--station", type=str, default="HSR Layout", help="Police station"
    )
    parser.add_argument("--closure", action="store_true", help="Requires road closure")
    parser.add_argument(
        "--hour", type=int, default=datetime.now().hour, help="Hour of day 0-23"
    )
    parser.add_argument(
        "--dow", type=int, default=datetime.now().weekday(), help="Day of week 0=Mon"
    )
    parser.add_argument(
        "--case",
        type=int,
        default=None,
        help="Run a specific test case by number (1-5). Default: runs all 5.",
    )
    parser.add_argument("--json", action="store_true", help="Also dump raw JSON output")
    args = parser.parse_args()
    classifier_mod, resolution_mod, resolution_artifacts, forecaster_mod = (
        load_all_models()
    )
    if args.desc:
        cases = [
            {
                "description": args.desc,
                "corridor": args.corridor,
                "police_station": args.station,
                "requires_road_closure": args.closure,
                "hour_of_day": args.hour,
                "day_of_week": args.dow,
            }
        ]
    elif args.case:
        cases = [TEST_CASES[args.case - 1]]
    else:
        cases = TEST_CASES
    for i, case in enumerate(cases, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST CASE {i}/{len(cases)}")
        print(f"{'=' * 60}")
        result = run_pipeline(
            **case,
            classifier_mod=classifier_mod,
            resolution_mod=resolution_mod,
            resolution_artifacts=resolution_artifacts,
            forecaster_mod=forecaster_mod,
        )
        pretty_print(result)
        if args.json:
            print("RAW JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"✓ Done. Ran {len(cases)} test case(s).")


if __name__ == "__main__":
    main()

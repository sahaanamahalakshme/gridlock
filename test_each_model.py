"""Script to independently test each ML model's inference."""

import sys
import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLASSIFIER_DIR = ROOT / "ml_models" / "bilingual_event_classifier"
RESOLUTION_DIR = ROOT / "ml_models" / "resolution_predictor"
FORECASTER_DIR = ROOT / "ml_models" / "impact_forecaster"


def import_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_classifier():
    print("\n" + "=" * 55)
    print("TEST: bilingual_event_classifier")
    print("=" * 55)
    mod = import_module_from_path("predict_clf", CLASSIFIER_DIR / "predict.py")
    inputs = [
        "Vehicle breakdown on Mysore road near toll gate",
        "ವಾಹನ ಕೆಟ್ಟು ನಿಂತಿದೆ ಸರ್",
        "ರಸ್ತೆ ಅಪಘಾತ ಆಗಿದೆ, ಸಂಚಾರ ನಿಧಾನ",
        "Heavy rain causing waterlogging at Koramangala",
        "Road blocked due to fallen tree",
        "Cricket match at stadium, high footfall",
        "VIP movement from airport",
        "Pothole causing traffic slow",
        "Construction work blocking one lane near silk board",
        "",
    ]
    passed = 0
    failed = 0
    for text in inputs:
        try:
            result = mod.classify(text)
            cause = result["event_cause"]
            sev = result["severity"]
            c_conf = result["cause_confidence"]
            s_conf = result["severity_confidence"]
            assert isinstance(cause, str) and len(cause) > 0, "cause is empty"
            assert sev in ("High", "Low", "unknown"), f"unexpected severity: {sev}"
            assert 0.0 <= c_conf <= 1.0, f"cause confidence out of range: {c_conf}"
            assert 0.0 <= s_conf <= 1.0, f"severity confidence out of range: {s_conf}"
            assert "top3_causes" in result, "missing top3_causes"
            status = "✓ PASS"
            passed += 1
        except AssertionError as e:
            status = f"✗ FAIL  ({e})"
            failed += 1
        except Exception as e:
            status = f"✗ ERROR ({e})"
            failed += 1
        label_text = repr(text[:50]) if text else repr("")
        print(f"  {status}  | input={label_text}")
        if "result" in dir() and result:
            print(
                f"            → cause={result.get('event_cause')} ({result.get('cause_confidence', 0) * 100:.1f}%)  severity={result.get('severity')} ({result.get('severity_confidence', 0) * 100:.1f}%)"
            )
    print(f"\n  Result: {passed} passed, {failed} failed")
    return failed == 0


def test_resolution():
    print("\n" + "=" * 55)
    print("TEST: resolution_predictor")
    print("=" * 55)
    mod = import_module_from_path("predict_res", RESOLUTION_DIR / "src" / "predict.py")
    artifacts = mod.load_artifacts(model_dir=str(RESOLUTION_DIR / "models"))
    inputs = [
        {
            "event_cause": "vehicle_breakdown",
            "corridor": "Mysore Road",
            "priority": "High",
            "requires_road_closure": False,
            "police_station": "Kengeri",
            "hour_of_day": 8,
            "day_of_week": 1,
        },
        {
            "event_cause": "accident",
            "corridor": "ORR East 1",
            "priority": "High",
            "requires_road_closure": True,
            "police_station": "HSR Layout",
            "hour_of_day": 17,
            "day_of_week": 3,
        },
        {
            "event_cause": "tree_fall",
            "corridor": "CBD 1",
            "priority": "Low",
            "requires_road_closure": True,
            "police_station": "Cubbon Park",
            "hour_of_day": 14,
            "day_of_week": 2,
        },
        {
            "event_cause": "water_logging",
            "corridor": "Hebbal",
            "priority": "High",
            "requires_road_closure": False,
            "police_station": "Hebbal",
            "hour_of_day": 6,
            "day_of_week": 0,
        },
        {
            "event_cause": "public_event",
            "corridor": "CBD 2",
            "priority": "High",
            "requires_road_closure": False,
            "police_station": "Shivajinagar",
            "hour_of_day": 18,
            "day_of_week": 6,
        },
        {
            "event_cause": "alien_invasion",
            "corridor": "Unknown Road",
            "priority": "High",
            "requires_road_closure": True,
            "police_station": "Unknown",
            "hour_of_day": 12,
            "day_of_week": 4,
        },
    ]
    passed = 0
    failed = 0
    for ev in inputs:
        try:
            result = mod.predict(artifacts, ev)
            mins = result["predicted_minutes"]
            band = result["confidence_band"]
            method = result["method"]
            assert (
                isinstance(mins, float) and mins > 0
            ), f"predicted_minutes invalid: {mins}"
            assert (
                len(band) == 2 and band[0] <= mins <= band[1] + 1
            ), f"band invalid: {band}"
            status = "✓ PASS"
            passed += 1
        except AssertionError as e:
            status = f"✗ FAIL  ({e})"
            failed += 1
            result = {}
        except Exception as e:
            status = f"✗ ERROR ({type(e).__name__}: {e})"
            failed += 1
            result = {}
        print(
            f"  {status}  | cause={ev['event_cause']:<20} corridor={ev['corridor']:<15}"
        )
        if result:
            print(
                f"            → {result.get('predicted_minutes')} min  band={result.get('confidence_band')}  method={result.get('method')}"
            )
    print(f"\n  Result: {passed} passed, {failed} failed")
    return failed == 0


def test_forecaster():
    print("\n" + "=" * 55)
    print("TEST: impact_forecaster")
    print("=" * 55)
    mod = import_module_from_path("retrieve", FORECASTER_DIR / "src" / "retrieve.py")
    mod.load_artifacts()
    inputs = [
        {
            "event_cause": "vehicle_breakdown",
            "corridor": "Mysore Road",
            "description": "Heavy vehicle breakdown blocking the road",
        },
        {
            "event_cause": "public_event",
            "corridor": "CBD 2",
            "description": "Cricket match at Chinnaswamy stadium",
        },
        {
            "event_cause": "tree_fall",
            "corridor": "Koramangala",
            "description": "Large tree fell blocking two lanes",
        },
        {
            "event_cause": "water_logging",
            "corridor": "Hebbal",
            "description": "ಒಳಚರಂಡಿ ತುಂಬಿ ರಸ್ತೆ ಮೇಲೆ ನೀರು ಬಂದಿದೆ",
        },
    ]
    passed = 0
    failed = 0
    for q in inputs:
        try:
            results = mod.retrieve_similar_event(
                event_cause=q["event_cause"],
                corridor=q["corridor"],
                description=q["description"],
                k=3,
            )
            assert isinstance(results, list), "result is not a list"
            assert len(results) > 0, "empty results returned"
            for r in results:
                assert "event_cause" in r, "missing event_cause in result"
                assert "similarity" in r, "missing similarity in result"
                assert (
                    0.0 <= r["similarity"] <= 1.0
                ), f"similarity out of range: {r['similarity']}"
            status = "✓ PASS"
            passed += 1
            top = results[0]
            print(f"  {status}  | query cause={q['event_cause']:<20}")
            print(
                f"            → best match: {top['event_cause']:<22} similarity={top['similarity']}"
            )
            if top.get("known_duration_minutes"):
                print(
                    f"              known_duration={top['known_duration_minutes']} min"
                )
        except AssertionError as e:
            status = f"✗ FAIL  ({e})"
            failed += 1
            print(f"  {status}  | query cause={q['event_cause']}")
        except Exception as e:
            status = f"✗ ERROR ({type(e).__name__}: {e})"
            failed += 1
            print(f"  {status}  | query cause={q['event_cause']}")
    print(f"\n  Result: {passed} passed, {failed} failed")
    return failed == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        choices=["classifier", "resolution", "forecaster", "all"],
        default="all",
        help="Which model to test (default: all)",
    )
    args = parser.parse_args()
    results = {}
    if args.model in ("classifier", "all"):
        results["classifier"] = test_classifier()
    if args.model in ("resolution", "all"):
        results["resolution"] = test_resolution()
    if args.model in ("forecaster", "all"):
        results["forecaster"] = test_forecaster()
    print("\n" + "=" * 55)
    print("SUMMARY")
    print("=" * 55)
    all_passed = True
    for name, ok in results.items():
        icon = "✓" if ok else "✗"
        print(f"  {icon}  {name}")
        if not ok:
            all_passed = False
    if all_passed:
        print("\n✓ All models are working correctly. Safe to wire to Person B's API.")
    else:
        print("\n✗ Some models have issues — fix these before wiring to the API.")
        sys.exit(1)


if __name__ == "__main__":
    main()

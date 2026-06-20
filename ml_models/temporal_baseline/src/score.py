"""
score.py
--------
Runtime module — called by app.py on every POST /events/report.

Loads baseline.json ONCE at server startup (load_baseline()),
then scores each incoming event with score_spike() in microseconds.

Usage in app.py:
    from ml_models.temporal_baseline.src.score import load_baseline, score_spike

    # At startup (once):
    baseline = load_baseline()

    # Per request:
    from datetime import datetime, timezone
    live_count = db.query("SELECT COUNT(*) FROM events WHERE corridor=? "
                          "AND start > NOW() - INTERVAL '60 minutes'", corridor)
    result = score_spike(baseline, corridor=event.corridor,
                         current_hour=datetime.now(timezone.utc).hour,
                         live_count=live_count)
    # result["spike_label"] → "spike" / "severe" / "elevated" / "normal"
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "baseline.json"
)


def load_baseline(path: str = BASELINE_PATH) -> dict:
    """
    Load baseline.json into memory.
    Call ONCE at server startup — not per request.
    Returns the full baseline dict.
    """
    with open(path) as f:
        data = json.load(f)
    n_corridors = len(data["corridors"])
    print(f"[baseline] Loaded. {n_corridors} corridors, {data['n_days']} days of history.")
    return data


def _get_label(spike_ratio: float, thresholds: dict) -> str:
    for label, (lo, hi) in thresholds.items():
        if lo <= spike_ratio < hi:
            return label
    return "severe"


def score_spike(
    baseline: dict,
    corridor: str,
    current_hour: int,
    live_count: int,
    live_window_minutes: int = 60,
) -> dict:
    """
    Score a new event against the temporal baseline for its corridor + hour.

    Parameters
    ----------
    baseline         : output of load_baseline()
    corridor         : corridor string from the incoming event (e.g. "Mysore Road")
    current_hour     : int 0–23, hour of the new event (UTC)
    live_count       : number of events on this corridor in the last live_window_minutes
                       (caller must query the DB for this; 0 is a safe default)
    live_window_minutes : window used to count live_count (default 60)

    Returns
    -------
    dict with keys: spike_ratio, spike_label, is_spike, baseline_avg, hour,
                    corridor, is_peak_hour, explanation
    """
    corridors  = baseline["corridors"]
    thresholds = baseline["thresholds"]
    system     = baseline["system"]

    # ── Look up baseline avg for this corridor + hour ────────────────────────
    corr_data = corridors.get(corridor, {})
    hour_data = corr_data.get(str(current_hour), corr_data.get(str(current_hour), corr_data.get(current_hour, None)))

    if hour_data is None:
        # Corridor or hour not in history — fall back to system-wide baseline
        sys_hour = system.get(str(current_hour), system.get(current_hour, {"avg_per_day": 0.0}))
        baseline_avg = sys_hour["avg_per_day"]
        is_peak_hour = False
        data_source  = "system_wide_fallback"
    else:
        baseline_avg = hour_data["avg_per_day"]
        is_peak_hour = hour_data["is_peak_hour"]
        data_source  = "corridor_specific"

    # ── Compute spike ratio ──────────────────────────────────────────────────
    # Scale live_count to per-day equivalent (live_count is over live_window_minutes)
    # avg_per_day was computed over 1-hour windows, so:
    # effective_hourly_rate = live_count * (60 / live_window_minutes)
    effective_rate = live_count * (60.0 / live_window_minutes)

    if baseline_avg == 0:
        # No historical events at this corridor+hour — any live event is extraordinary
        spike_ratio = float(live_count) if live_count > 0 else 0.0
    else:
        spike_ratio = round(effective_rate / baseline_avg, 2)

    spike_label = _get_label(spike_ratio, thresholds)
    is_spike    = spike_ratio >= thresholds["spike"][0]

    # ── Build explanation string ─────────────────────────────────────────────
    peak_note = (
        f" Note: {current_hour:02d}:00 is a known peak hour for this corridor."
        if is_peak_hour else ""
    )

    if data_source == "system_wide_fallback":
        context_note = (
            f"No specific history for '{corridor}' at {current_hour:02d}:00 — "
            f"using system-wide baseline ({baseline_avg:.2f} avg events/hr)."
        )
    else:
        context_note = (
            f"Historical baseline for {corridor} at {current_hour:02d}:00: "
            f"{baseline_avg:.2f} avg events/day."
        )

    if spike_ratio == 0:
        ratio_note = "No live events on this corridor in the last hour — quiet period."
    elif spike_label == "normal":
        ratio_note = (
            f"Current rate ({effective_rate:.1f} events/hr) is {spike_ratio:.1f}× "
            f"baseline — within normal range. Standard dispatch."
        )
    elif spike_label == "elevated":
        ratio_note = (
            f"Current rate ({effective_rate:.1f} events/hr) is {spike_ratio:.1f}× "
            f"baseline — slightly elevated. Monitor this corridor."
        )
    elif spike_label == "spike":
        ratio_note = (
            f"Current rate ({effective_rate:.1f} events/hr) is {spike_ratio:.1f}× "
            f"baseline — significant spike. Prioritise dispatch."
        )
    else:
        ratio_note = (
            f"Current rate ({effective_rate:.1f} events/hr) is {spike_ratio:.1f}× "
            f"baseline — severe spike. Escalate immediately."
        )

    explanation = f"{context_note} {ratio_note}{peak_note}"

    return {
        "spike_ratio":   spike_ratio,
        "spike_label":   spike_label,       # "normal" | "elevated" | "spike" | "severe"
        "is_spike":      is_spike,
        "baseline_avg":  round(baseline_avg, 4),
        "effective_rate": round(effective_rate, 2),
        "hour":          current_hour,
        "corridor":      corridor,
        "is_peak_hour":  is_peak_hour,
        "data_source":   data_source,
        "explanation":   explanation,
    }


# ── Smoke test — run this file directly ──────────────────────────────────────
if __name__ == "__main__":
    print("[score] Loading baseline for smoke test…")
    b = load_baseline()

    test_cases = [
        # (corridor, hour, live_count, description)
        ("Mysore Road",   21,  3, "Mysore Road at peak hour with 3 events → expect spike"),
        ("Mysore Road",   12,  1, "Mysore Road at quiet midday with 1 event → expect severe"),
        ("Bellary Road 1", 6,  4, "Bellary Rd at morning rush with 4 events → check"),
        ("Non-corridor",  21,  2, "Non-corridor at peak → check system fallback"),
        ("Unknown Road",   9,  0, "Unknown corridor no events → expect normal"),
    ]

    print()
    for corridor, hour, count, desc in test_cases:
        result = score_spike(b, corridor=corridor, current_hour=hour, live_count=count)
        print(f"  ── {desc}")
        print(f"     spike_ratio={result['spike_ratio']}  label={result['spike_label']}  "
              f"is_spike={result['is_spike']}")
        print(f"     {result['explanation']}")
        print()
"""
classifier_client.py
--------------------
Place at: gridlock/classifier_client.py

Drop-in replacement for:
    from ml_models.bilingual_event_classifier.predict import classify

Now matches the ACTUAL predict.py signature:
    classify(description: str, police_station: str = "") -> dict

The returned dict includes a "routing" key from routing_map.py,
which the HF Space handles internally — no change needed on this side.
"""

import os
import requests

HF_CLASSIFIER_URL = os.environ.get(
    "HF_CLASSIFIER_URL",
    "https://ratish-01-drishti-classifier.hf.space/classify"
)

_TIMEOUT = 20  # mpnet-base-v2 is larger, give it more time on cold start


def classify(description: str, police_station: str = "") -> dict:
    """
    Drop-in replacement for the local classify() function.
    Matches the exact signature of predict.py including police_station.

    Returns same shape as local predict.py:
    {
        "event_cause":         str,
        "cause_confidence":    float,
        "severity":            str,
        "severity_confidence": float,
        "top3_causes":         list,
        "routing":             str,   ← from routing_map.py on HF side
    }
    """
    if not description or not description.strip():
        return {
            "event_cause":         "unknown",
            "cause_confidence":    0.0,
            "severity":            "unknown",
            "severity_confidence": 0.0,
            "top3_causes":         [],
            "routing":             "Traffic Police",
            "error":               "Empty description",
        }

    try:
        response = requests.post(
            HF_CLASSIFIER_URL,
            json={
                "description": description.strip(),
                "police_station": police_station or "",
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        return _fallback("HF Space timeout — it may be waking from sleep, retry in 30s")
    except requests.exceptions.ConnectionError:
        return _fallback("Cannot reach HF classifier — check HF_CLASSIFIER_URL env var")
    except requests.exceptions.HTTPError as e:
        return _fallback(f"HF classifier returned HTTP {e.response.status_code}")
    except Exception as e:
        return _fallback(str(e))


def _fallback(reason: str) -> dict:
    return {
        "event_cause":         "unknown",
        "cause_confidence":    0.0,
        "severity":            "unknown",
        "severity_confidence": 0.0,
        "top3_causes":         [],
        "routing":             "Traffic Police",
        "error":               reason,
    }


def health_check() -> dict:
    """Ping the HF Space health endpoint."""
    url = HF_CLASSIFIER_URL.replace("/classify", "/health")
    try:
        r = requests.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        return {"hf_classifier": "ok", **r.json()}
    except Exception as e:
        return {"hf_classifier": "unreachable", "error": str(e)}
"""
retriever_client.py
====================
HTTP client for the impact-forecaster service deployed as its own
HuggingFace Space ("drishti-retriever"), mirroring the same pattern
already used by classifier_client.py for the bilingual classifier.

WHY this exists instead of importing ml_models.impact_forecaster.src.retrieve
directly: that local import pulls in sentence_transformers + torch, which
is what crashed the Render deploy (ModuleNotFoundError: sentence_transformers).
Render's backend should stay a thin orchestrator calling lightweight HTTP
endpoints, not bundle every model's heavy dependencies itself.

Add to Render's requirements.txt: httpx==0.27.0
"""

import os
import httpx

# Set this as an environment variable on Render once the Space is live,
# e.g. RETRIEVER_URL=https://ratish-01-drishti-retriever.hf.space
# Falling back to a placeholder so failures are loud, not silent.
RETRIEVER_URL = os.environ.get(
    "RETRIEVER_URL", "https://ratish-01-drishti-retriever.hf.space"
)

_TIMEOUT = httpx.Timeout(30.0)


def retrieve_similar_event(event_cause: str, corridor: str, description: str, k: int = 3):
    """
    Synchronous call to the deployed impact-forecaster Space.

    Kept synchronous (not async) to match how retrieve_similar_event was
    called previously in app.py -- swap to async + httpx.AsyncClient if/when
    the surrounding endpoint functions are made async.
    """
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.post(
                f"{RETRIEVER_URL}/retrieve",
                json={
                    "event_cause": event_cause,
                    "corridor": corridor,
                    "description": description,
                    "k": k,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        # Fail loud but don't crash the whole /events/report endpoint --
        # return an empty match list so the rest of the pipeline (resolution
        # prediction, classification, memory write) still completes.
        print(f"[retriever_client] WARNING: retriever call failed: {e}")
        return []
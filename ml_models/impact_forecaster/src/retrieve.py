import os
import joblib

import pandas as pd

from sentence_transformers import SentenceTransformer


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PATH = os.path.join(ROOT_DIR, "models", "train_meta.csv")
INDEX_PATH = os.path.join(ROOT_DIR, "models", "nn_index.joblib")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


_model = None

_index = None

_meta = None


def load_artifacts():

    global _model, _index, _meta

    if _model is None:

        _model = SentenceTransformer(MODEL_NAME)

        _index = joblib.load(INDEX_PATH)

        _meta = pd.read_csv(META_PATH)


def retrieve_similar_event(
    event_cause: str, corridor: str, description: str, k: int = 3
):

    load_artifacts()

    query_text = f"{event_cause } | {corridor } | {description }"

    query_embedding = _model.encode([query_text], normalize_embeddings=True)

    distances, indices = _index.kneighbors(query_embedding, n_neighbors=k)

    results = []

    for dist, idx in zip(distances[0], indices[0]):

        row = _meta.iloc[idx]

        results.append(
            {
                "matched_event_id": row["id"],
                "event_cause": row["event_cause"],
                "corridor": row["corridor"],
                "description": row["description"],
                "known_duration_minutes": (
                    row["duration_minutes"]
                    if pd.notna(row["duration_minutes"])
                    else None
                ),
                "similarity": round(1 - dist, 4),
            }
        )

    return results


if __name__ == "__main__":

    example = retrieve_similar_event(
        event_cause="public_event",
        corridor="CBD 2",
        description="Cricket match at stadium, high footfall expected",
        k=3,
    )

    for r in example:

        print(r)

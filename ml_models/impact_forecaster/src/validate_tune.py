import joblib

import numpy as np

import pandas as pd

from sentence_transformers import SentenceTransformer


VAL_PATH = "data/splits/val.csv"

META_PATH = "models/train_meta.csv"

INDEX_PATH = "models/nn_index.joblib"

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


K_VALUES_TO_TRY = [1, 3, 5]


def evaluate(k_values=K_VALUES_TO_TRY):

    val_df = pd.read_csv(VAL_PATH)

    train_meta = pd.read_csv(META_PATH)

    nn = joblib.load(INDEX_PATH)

    model = SentenceTransformer(MODEL_NAME)

    val_embeddings = model.encode(
        val_df["retrieval_text"].tolist(), normalize_embeddings=True
    )

    max_k = max(k_values)

    distances, indices = nn.kneighbors(val_embeddings, n_neighbors=max_k)

    for k in k_values:

        cause_hits = 0

        duration_errors = []

        for row_i, query_row in val_df.reset_index(drop=True).iterrows():

            neighbor_idx = indices[row_i][:k]

            neighbors = train_meta.iloc[neighbor_idx]

            if neighbors.iloc[0]["event_cause"] == query_row["event_cause"]:

                cause_hits += 1

            neighbors_with_duration = neighbors[neighbors["duration_minutes"].notna()]

            if (
                pd.notna(query_row["duration_minutes"])
                and len(neighbors_with_duration) > 0
            ):

                predicted = neighbors_with_duration.iloc[0]["duration_minutes"]

                duration_errors.append(abs(predicted - query_row["duration_minutes"]))

        cause_accuracy = cause_hits / len(val_df)

        mae = np.mean(duration_errors) if duration_errors else float("nan")

        print(
            f"k={k :>2}  top-1 cause match={cause_accuracy :.2%}  "
            f"duration MAE={mae :.1f} min (n={len (duration_errors )})"
        )


if __name__ == "__main__":

    evaluate()

import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

TEST_PATH = "data/splits/test.csv"
META_PATH = "models/train_meta.csv"
INDEX_PATH = "models/nn_index.joblib"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

BEST_K = 3


def final_evaluate():
    test_df = pd.read_csv(TEST_PATH)
    train_meta = pd.read_csv(META_PATH)
    nn = joblib.load(INDEX_PATH)

    model = SentenceTransformer(MODEL_NAME)
    test_embeddings = model.encode(test_df["retrieval_text"].tolist(), normalize_embeddings=True)

    distances, indices = nn.kneighbors(test_embeddings, n_neighbors=BEST_K)

    cause_hits = 0
    duration_errors = []

    for row_i, query_row in test_df.reset_index(drop=True).iterrows():
        neighbors = train_meta.iloc[indices[row_i]]

        if neighbors.iloc[0]["event_cause"] == query_row["event_cause"]:
            cause_hits += 1

        neighbors_with_duration = neighbors[neighbors["duration_minutes"].notna()]
        if pd.notna(query_row["duration_minutes"]) and len(neighbors_with_duration) > 0:
            predicted = neighbors_with_duration.iloc[0]["duration_minutes"]
            duration_errors.append(abs(predicted - query_row["duration_minutes"]))

    print(f"FINAL TEST (k={BEST_K}, n={len(test_df)})")
    print(f"top-1 cause match: {cause_hits / len(test_df):.2%}")
    if duration_errors:
        print(f"duration MAE: {np.mean(duration_errors):.1f} min (n={len(duration_errors)})")
    else:
        print("duration MAE: no test rows had both a real and a retrieved duration")


if __name__ == "__main__":
    final_evaluate()
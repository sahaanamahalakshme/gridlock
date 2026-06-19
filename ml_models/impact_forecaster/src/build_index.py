import joblib

import numpy as np

import pandas as pd

from sentence_transformers import SentenceTransformer

from sklearn.neighbors import NearestNeighbors


TRAIN_PATH = "data/splits/train.csv"

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


EMBED_OUT = "models/train_embeddings.npy"

INDEX_OUT = "models/nn_index.joblib"

META_OUT = "models/train_meta.csv"


def build():

    train_df = pd.read_csv(TRAIN_PATH)

    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        train_df["retrieval_text"].tolist(),
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    nn = NearestNeighbors(n_neighbors=5, metric="cosine")

    nn.fit(embeddings)

    np.save(EMBED_OUT, embeddings)

    joblib.dump(nn, INDEX_OUT)

    train_df.to_csv(META_OUT, index=False)

    print(
        f"indexed {len (train_df )} training events, embedding dim {embeddings .shape [1 ]}"
    )


if __name__ == "__main__":

    build()

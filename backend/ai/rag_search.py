import json
import faiss
import numpy as np

from pathlib import Path
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[2]

RAG_DIR = BASE_DIR / "data/processed/rag"

INDEX_FILE = RAG_DIR / "events_index.faiss"
METADATA_FILE = RAG_DIR / "events_metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"


def load_rag():

    index = faiss.read_index(
        str(INDEX_FILE)
    )

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        metadata = json.load(f)

    model = SentenceTransformer(
        MODEL_NAME
    )

    return index, metadata, model


def search_events(query, top_k=5):

    index, metadata, model = load_rag()

    embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    embedding = np.asarray(
        embedding,
        dtype="float32"
    )

    faiss.normalize_L2(
        embedding
    )

    scores, indices = index.search(
        embedding,
        top_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0 or idx >= len(metadata):
            continue

        result = metadata[idx].copy()

        result["similarity_score"] = float(
            score
        )

        results.append(result)

    return results


def main():

    print("=" * 80)
    print("eRTMAC-NWIS | HISTORICAL DRILLING EVENT SEARCH")
    print("=" * 80)

    query = (
        "pressure event during drilling "
        "high pump pressure and flow changes"
    )

    print("\nQuery:")
    print(query)

    results = search_events(
        query,
        top_k=5
    )

    print("\nTop historical matches:\n")

    for i, result in enumerate(
        results,
        start=1
    ):

        print("-" * 70)

        print(
            f"Match #{i}"
        )

        print(
            f"Similarity : "
            f"{result['similarity_score']:.4f}"
        )

        print(
            f"Well       : "
            f"{result['well_id']}"
        )

        print(
            f"Event      : "
            f"{result['event_type']}"
        )

        print(
            f"Depth      : "
            f"{result['event_md']} m"
        )

        print(
            f"Timestamp  : "
            f"{result['timestamp']}"
        )

        print(
            f"Description: "
            f"{result['description']}"
        )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

import pandas as pd
import numpy as np
import faiss

from pathlib import Path
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[2]

EVENT_FILE = BASE_DIR / "data/processed/drilling_events_with_depth.csv"

RAG_DIR = BASE_DIR / "data/processed/rag"

INDEX_FILE = RAG_DIR / "events_index.faiss"
METADATA_FILE = RAG_DIR / "events_metadata.json"


MODEL_NAME = "all-MiniLM-L6-v2"


def main():

    print("=" * 80)
    print("eRTMAC-NWIS | BUILDING RAG KNOWLEDGE INDEX")
    print("=" * 80)

    # ---------------------------------------------------------
    # LOAD EVENTS
    # ---------------------------------------------------------

    print("\nLoading drilling events...")

    df = pd.read_csv(EVENT_FILE)

    print("Events loaded:", len(df))

    # ---------------------------------------------------------
    # CREATE TEXT DOCUMENTS
    # ---------------------------------------------------------

    documents = []
    metadata = []

    for _, row in df.iterrows():

        well_id = str(row.get("well_id", "Unknown"))
        event_type = str(row.get("event_type", "Unknown"))

        event_md = row.get("event_md", "")
        timestamp = row.get("timestamp", "")

        description = str(
            row.get("description", "")
        )

        text = (
            f"Well: {well_id}. "
            f"Event type: {event_type}. "
            f"Measured depth: {event_md} m. "
            f"Timestamp: {timestamp}. "
            f"Description: {description}."
        )

        documents.append(text)

        metadata.append({
            "well_id": well_id,
            "event_type": event_type,
            "event_md": event_md,
            "timestamp": timestamp,
            "description": description,
            "text": text
        })

    print("Documents created:", len(documents))

    # ---------------------------------------------------------
    # LOAD EMBEDDING MODEL
    # ---------------------------------------------------------

    print("\nLoading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print("Embedding model loaded.")

    # ---------------------------------------------------------
    # CREATE EMBEDDINGS
    # ---------------------------------------------------------

    print("\nCreating embeddings...")

    embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    print(
        "Embedding shape:",
        embeddings.shape
    )

    # ---------------------------------------------------------
    # NORMALIZE
    # ---------------------------------------------------------

    faiss.normalize_L2(
        embeddings
    )

    # ---------------------------------------------------------
    # CREATE FAISS INDEX
    # ---------------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(
        embeddings
    )

    print(
        "FAISS vectors:",
        index.ntotal
    )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    RAG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(
        index,
        str(INDEX_FILE)
    )

    import json

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n" + "=" * 80)
    print("RAG INDEX CREATED SUCCESSFULLY")
    print("=" * 80)

    print("\nFAISS index:")
    print(INDEX_FILE)

    print("\nMetadata:")
    print(METADATA_FILE)

    print("\nVectors:", index.ntotal)
    print("Dimension:", dimension)


if __name__ == "__main__":
    main()

# app/rag_retriever.py
import faiss
import pickle
import json
import os
from typing import List, Dict, Any
from google.cloud import storage


def ensure_file_from_gcs(bucket_name: str, gcs_name: str, local_path: str):
    """
    If local_path does not exist, download gs://{bucket_name}/{gcs_name} to local_path.
    """
    if os.path.exists(local_path):
        return
    if not bucket_name:
        raise RuntimeError("GCS_BUCKET not set and local file missing: " + local_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_name)
    if not blob.exists():
        raise FileNotFoundError(f"{gcs_name} not found in bucket {bucket_name}")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    blob.download_to_filename(local_path)
    # optional: log
    print(f"Downloaded gs://{bucket_name}/{gcs_name} -> {local_path}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

FAISS_PATH = os.path.join(DATA_DIR, "drilling_index.faiss")
EMB_PATH = os.path.join(DATA_DIR, "drilling_embeddings.pkl")
META_PATH = os.path.join(DATA_DIR, "drilling_metadata.json")
MODEL_INFO_PATH = os.path.join(DATA_DIR, "embedding_model.txt")

GCS_BUCKET = os.getenv("GCS_BUCKET", None)

# ensure files exist locally (download from GCS if not)
ensure_file_from_gcs(GCS_BUCKET, "drilling_index.faiss", FAISS_PATH)
ensure_file_from_gcs(GCS_BUCKET, "drilling_metadata.json", META_PATH)
# optional: embeddings & model info
try:
    ensure_file_from_gcs(GCS_BUCKET, "drilling_embeddings.pkl", EMB_PATH)
except Exception:
    pass


# Load FAISS index (assume already created)
if not os.path.exists(FAISS_PATH):
    raise FileNotFoundError(f"FAISS index not found at {FAISS_PATH}")
index = faiss.read_index(FAISS_PATH)

# optional debug loads
try:
    with open(EMB_PATH, "rb") as f:
        embeddings = pickle.load(f)
except Exception:
    embeddings = None

with open(META_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)  # expect list aligned to faiss ids


def _get_chunk_text(meta_entry: dict) -> str:
    for k in ("content", "text", "chunk", "body", "passage"):
        if k in meta_entry and meta_entry[k]:
            return meta_entry[k]
    # fallback: join string-ish fields
    parts = [v for v in meta_entry.values() if isinstance(v, str) and len(v) > 10]
    return " ".join(parts) if parts else ""


# Lazy-loaded embedding model variable
_embedding_model = None


def _load_embedding_model():
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model

    # Read model path/name from file
    if not os.path.exists(MODEL_INFO_PATH):
        raise FileNotFoundError(
            f"Missing {MODEL_INFO_PATH}. Put the local model path or HF name in that file."
        )

    with open(MODEL_INFO_PATH, "r") as f:
        model_name = f.read().strip()

    # prefer local path; SentenceTransformer will try HF if given a hub id
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError(
            "sentence-transformers not installed. install with: pip install sentence-transformers"
        ) from e

    # If model_name is a local path, this will load from disk with no HF download.
    _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def query_rag(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Return list of {"score": float, "metadata": {...}, "content": "<text>"}.
    """
    # Encode query using locally available embedding model (lazy load)
    try:
        model = _load_embedding_model()
    except Exception as e:
        raise RuntimeError(
            "Failed to load embedding model. Make sure MODEL_INFO_PATH points to a local model path or install HF credentials."
        ) from e

    q_emb = model.encode([query])
    # ensure float32 numpy
    import numpy as np

    q_emb = np.asarray(q_emb, dtype="float32")
    D, I = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(D[0], I[0]):
        entry_meta = metadata[idx] if idx < len(metadata) else {}
        content = _get_chunk_text(entry_meta)
        results.append(
            {"score": float(score), "metadata": entry_meta, "content": content}
        )
    return results

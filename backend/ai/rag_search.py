import json
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

BASE_DIR = Path(__file__).resolve().parents[2]
RAG_DIR = BASE_DIR / "data/processed/rag"
INDEX_FILE = RAG_DIR / "events_index.faiss"
METADATA_FILE = RAG_DIR / "events_metadata.json"
MODEL_NAME = "all-MiniLM-L6-v2"

_rag_cache = None


def load_rag():
    global _rag_cache
    if _rag_cache is not None:
        return _rag_cache

    try:
        import faiss
        from sentence_transformers import SentenceTransformer

        if not INDEX_FILE.exists() or not METADATA_FILE.exists():
            raise FileNotFoundError("RAG index or metadata file not found.")

        index = faiss.read_index(str(INDEX_FILE))
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        model = SentenceTransformer(MODEL_NAME)
        _rag_cache = (index, metadata, model)
        return _rag_cache
    except Exception as e:
        # Load metadata once so fallback search does not re-read from disk on every query
        metadata = []
        if METADATA_FILE.exists():
            try:
                with open(METADATA_FILE, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception:
                pass
        _rag_cache = (None, metadata, None)
        return _rag_cache


def search_events(query, top_k=5):
    index, metadata, model = load_rag()

    if index is not None and model is not None and np is not None and metadata:
        try:
            embedding = model.encode([query], convert_to_numpy=True)
            embedding = np.asarray(embedding, dtype="float32")
            import faiss
            faiss.normalize_L2(embedding)
            scores, indices = index.search(embedding, top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(metadata):
                    continue
                result = metadata[idx].copy()
                result["similarity_score"] = float(score)
                results.append(result)
            if results:
                return results
        except Exception:
            pass  # Fall through to metadata search

    # Fallback search directly over events_metadata.json using keyword relevance
    meta = metadata
    if not meta and METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            return []

    if not meta:
        return []

    # Keyword / term-overlap scoring
    query_tokens = [w.strip() for w in query.lower().replace(",", " ").replace(".", " ").split() if len(w.strip()) > 2]
    scored = []
    for item in meta:
        text = (item.get("text") or item.get("description") or "").lower()
        event_type = (item.get("event_type") or "").lower()
        score = sum(1.0 for token in query_tokens if token in text)
        if event_type in query.lower():
            score += 2.0
        if score > 0:
            entry = item.copy()
            entry["similarity_score"] = round(min(0.95, 0.45 + 0.10 * score), 3)
            scored.append(entry)

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    if not scored:
        return [dict(item, similarity_score=0.5) for item in meta[:top_k]]
    return scored[:top_k]


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

    results = search_events(query, top_k=5)
    print("\nTop historical matches:\n")

    for i, result in enumerate(results, start=1):
        print("-" * 70)
        print(f"Match #{i}")
        print(f"Similarity : {result['similarity_score']:.4f}")
        print(f"Well       : {result['well_id']}")
        print(f"Event      : {result['event_type']}")
        print(f"Depth      : {result['event_md']} m")
        print(f"Timestamp  : {result['timestamp']}")
        print(f"Description: {result['description']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

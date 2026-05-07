import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.services.embeddings import model, _profile_chunks, RETRIEVAL_THRESHOLD

def evaluate_retrieval(question: str, retrieved_sections: list[dict], retrieved_chunks: list[str]) -> dict:
    """
    Measures retrieval quality without ground truth.
    
    1. Relevance score — avg cosine sim between question and retrieved chunks
    2. Coverage — what % of profile was retrieved (lower = more selective = better for specific Qs)
    3. Threshold pass rate — how many chunks scored above threshold vs total
    """
    if not retrieved_chunks or not _profile_chunks:
        return {"error": "Nothing to evaluate"}

    query_vec = model.encode([question], convert_to_numpy=True)
    query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)

    chunk_vecs = model.encode(retrieved_chunks, convert_to_numpy=True)
    chunk_vecs = chunk_vecs / np.linalg.norm(chunk_vecs, axis=1, keepdims=True)

    sims = cosine_similarity(query_vec, chunk_vecs)[0]

    return {
        "avg_relevance_score": round(float(np.mean(sims)), 3),
        "min_relevance_score": round(float(np.min(sims)), 3),
        "max_relevance_score": round(float(np.max(sims)), 3),
        "chunks_retrieved": len(retrieved_chunks),
        "total_chunks_available": len(_profile_chunks),
        "coverage_percent": round(len(retrieved_chunks) / len(_profile_chunks) * 100, 1),
        "retrieval_mode": "broad" if len(retrieved_chunks) == len(_profile_chunks) else "selective"
    }


def evaluate_hallucination(answer: str, actual_columns: list[str]) -> dict:
    """
    Scans LLM answer for column name references.
    Flags any column mentioned that doesn't exist in dataset.
    """
    import re
    # find backtick-wrapped words (how LLMs typically reference columns)
    mentioned = re.findall(r"`([^`]+)`", answer)
    
    invented = [m for m in mentioned if m not in actual_columns]
    valid = [m for m in mentioned if m in actual_columns]

    return {
        "columns_mentioned": mentioned,
        "valid_references": valid,
        "hallucinated_references": invented,
        "hallucination_detected": len(invented) > 0
    }
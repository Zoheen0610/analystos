import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# column search index
_column_names = []
_column_index = None

# profile chunk index for RAG
_profile_chunks = []       # list of {"section": str, "content": str}
_profile_chunk_index = None

RETRIEVAL_THRESHOLD = 0.35  # below this = not relevant, don't send to LLM

def build_column_index(columns: list[str]):
    global _column_names, _column_index
    _column_names = columns
    embeddings = model.encode(columns, convert_to_numpy=True)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    dim = embeddings.shape[1]
    _column_index = faiss.IndexFlatIP(dim)
    _column_index.add(embeddings)

def search_columns(query: str, top_k: int = 5) -> list[dict]:
    if _column_index is None or not _column_names:
        return []
    query_vec = model.encode([query], convert_to_numpy=True)
    query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)
    scores, indices = _column_index.search(query_vec, min(top_k, len(_column_names)))
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx != -1 and float(score) >= RETRIEVAL_THRESHOLD:
            results.append({
                "column": _column_names[idx],
                "similarity": round(float(score), 3)
            })
    if not results:
        return [{"message": "No sufficiently similar columns found", 
                 "threshold": RETRIEVAL_THRESHOLD}]
    return results

def build_profile_chunks(profile: dict):
    """
    Split profile into meaningful semantic chunks.
    Each chunk = one aspect of the dataset.
    This is what gets retrieved selectively for RAG.
    """
    global _profile_chunks, _profile_chunk_index
    _profile_chunks = []

    # chunk 1 — shape overview
    _profile_chunks.append({
        "section": "dataset_overview",
        "content": (
            f"Dataset has {profile['shape']['rows']} rows and "
            f"{profile['shape']['columns']} columns. "
            f"Columns: {', '.join(profile['columns'])}. "
            f"Duplicate rows: {profile.get('duplicates', 0)}."
        )
    })

    # chunk 2 — missing values
    if profile.get("missing"):
        missing_text = ". ".join([
            f"{col} has {info['count']} missing values ({info['percent']}%)"
            for col, info in profile["missing"].items()
        ])
        _profile_chunks.append({
            "section": "missing_values",
            "content": f"Missing value analysis: {missing_text}"
        })

    # chunk 3 — skewness
    if profile.get("skewness"):
        skew_text = ". ".join([
            f"{col} has skewness of {val}"
            for col, val in profile["skewness"].items()
        ])
        _profile_chunks.append({
            "section": "skewness",
            "content": f"Skewness analysis (columns with skew > 1): {skew_text}"
        })

    # chunk 4 — outliers
    if profile.get("outliers"):
        outlier_text = ". ".join([
            f"{col} has {count} outliers"
            for col, count in profile["outliers"].items()
        ])
        _profile_chunks.append({
            "section": "outliers",
            "content": f"Outlier analysis: {outlier_text}"
        })

    # chunk 5 — correlations
    if profile.get("correlations"):
        corr_text = ". ".join([
            f"{c['col1']} and {c['col2']} correlation: {c['correlation']}"
            for c in profile["correlations"][:5]
        ])
        _profile_chunks.append({
            "section": "correlations",
            "content": f"Feature correlations (above 0.6): {corr_text}"
        })

    # chunk 6 — data types
    if profile.get("dtypes"):
        dtype_text = ", ".join([
            f"{col}: {dtype}"
            for col, dtype in profile["dtypes"].items()
        ])
        _profile_chunks.append({
            "section": "data_types",
            "content": f"Column data types: {dtype_text}"
        })

    # embed all chunks
    chunk_texts = [c["content"] for c in _profile_chunks]
    embeddings = model.encode(chunk_texts, convert_to_numpy=True)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    dim = embeddings.shape[1]
    _profile_chunk_index = faiss.IndexFlatIP(dim)
    _profile_chunk_index.add(embeddings)

def retrieve_relevant_chunks(query: str, top_k: int = 3) -> dict:
    """
    Retrieve only the profile sections relevant to the query.
    Returns chunks above threshold + metadata about what was retrieved.
    """
    if _profile_chunk_index is None or not _profile_chunks:
        return {"chunks": [], "retrieved_sections": [], "warning": "Profile not indexed yet"}

    query_vec = model.encode([query], convert_to_numpy=True)
    query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)

    scores, indices = _profile_chunk_index.search(
        query_vec, min(top_k, len(_profile_chunks))
    )

    retrieved = []
    retrieved_sections = []
    for score, idx in zip(scores[0], indices[0]):
        if idx != -1 and float(score) >= RETRIEVAL_THRESHOLD:
            chunk = _profile_chunks[idx]
            retrieved.append(chunk["content"])
            retrieved_sections.append({
                "section": chunk["section"],
                "similarity": round(float(score), 3)
            })

    if not retrieved:
        # fallback — return overview chunk so LLM isn't totally blind
        retrieved = [_profile_chunks[0]["content"]]
        retrieved_sections = [{"section": "dataset_overview", "similarity": 0.0}]

    return {
        "chunks": retrieved,
        "retrieved_sections": retrieved_sections
    }
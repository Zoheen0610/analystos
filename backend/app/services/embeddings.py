import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
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
            f"Active dataset filename: {profile.get('filename', 'unknown')}. "
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
    if _profile_chunk_index is None or not _profile_chunks:
        return {"chunks": [], "retrieved_sections": [], "warning": "Profile not indexed yet"}

    query_vec = model.encode([query], convert_to_numpy=True)
    query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)

    # search all chunks
    scores, indices = _profile_chunk_index.search(
        query_vec, len(_profile_chunks)  # search ALL, not just top_k
    )

    retrieved = []
    retrieved_sections = []
    for score, idx in zip(scores[0], indices[0]):
        if idx != -1 and float(score) >= RETRIEVAL_THRESHOLD:
            retrieved.append(_profile_chunks[idx]["content"])
            retrieved_sections.append({
                "section": _profile_chunks[idx]["section"],
                "similarity": round(float(score), 3)
            })

    # if nothing retrieved OR it's a broad/summary question — return everything
    broad_keywords = {"summary", "stats", "overview", "all", "everything", 
                      "describe", "tell me about", "what is", "explain"}
    query_lower = query.lower()
    is_broad = not retrieved or any(kw in query_lower for kw in broad_keywords)

    if is_broad:
        retrieved = [c["content"] for c in _profile_chunks]
        retrieved_sections = [
            {"section": c["section"], "similarity": "broad_query"} 
            for c in _profile_chunks
        ]

    # cap at top_k after broad check
    return {
        "chunks": retrieved[:top_k] if not is_broad else retrieved,
        "retrieved_sections": retrieved_sections
    }
GRAPH_RETRIEVAL_THRESHOLD = 0.35

def node_to_text(node: dict) -> str:
    if node["type"] == "profiling":
        parts = []
        if node.get("missing_columns"):
            parts.append(f"missing data in {', '.join(node['missing_columns'])}")
        if node.get("skewed_columns"):
            parts.append(f"skewed columns {', '.join(node['skewed_columns'])}")
        if node.get("outlier_columns"):
            parts.append(f"outliers in {', '.join(node['outlier_columns'])}")
        if node.get("top_correlations"):
            parts.append("correlations: " + ", ".join([
                f"{c['col1']} and {c['col2']} at {c['correlation']}"
                for c in node["top_correlations"]
            ]))
        return f"Dataset profiling: {'. '.join(parts)}" if parts else ""

    elif node["type"] == "session_summary":
        return f"Past session on {node.get('date', '')}: {node.get('summary', '')}"

    return ""


def retrieve_relevant_graph_nodes(question: str, graph_state: dict, top_k: int = 2) -> list[str]:
    if not graph_state:
        return []

    node_texts = []
    for node in graph_state.get("nodes", []):
        text = node_to_text(node)
        if text:
            node_texts.append(text)

    if not node_texts:
        return []

    node_vecs = model.encode(node_texts, convert_to_numpy=True)
    node_vecs = node_vecs / np.linalg.norm(node_vecs, axis=1, keepdims=True)

    query_vec = model.encode([question], convert_to_numpy=True)
    query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)

    scores = cosine_similarity(query_vec, node_vecs)[0]

    return [
        node_texts[i] for i in np.argsort(scores)[::-1]
        if scores[i] >= GRAPH_RETRIEVAL_THRESHOLD
    ][:top_k]
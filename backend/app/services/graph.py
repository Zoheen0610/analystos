import networkx as nx
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

workflow_graph = nx.DiGraph()
# with this
_node_counters = {}

def _new_id(prefix: str) -> str:
    _node_counters[prefix] = _node_counters.get(prefix, 0) + 1
    return f"{prefix}_{_node_counters[prefix]}"
_session_questions = []

# stores summary node embeddings for comparison
# format: {"node_id": {"date": "...", "summary": "...", "embedding": [...]}}
_summary_store = {}



def add_dataset_node(filename: str, shape: dict) -> str:
    node_id = _new_id("dataset")
    workflow_graph.add_node(node_id,
        type="dataset",
        filename=filename,
        rows=shape["rows"],
        columns=shape["columns"],
        timestamp=datetime.now().isoformat()
    )
    return node_id

def add_profiling_node(dataset_node_id: str, profile_summary: dict) -> str:
    node_id = _new_id("profiling")
    workflow_graph.add_node(node_id,
        type="profiling",
        missing_columns=list(profile_summary.get("missing", {}).keys()),
        skewed_columns=list(profile_summary.get("skewness", {}).keys()),
        outlier_columns=list(profile_summary.get("outliers", {}).keys()),
        top_correlations=profile_summary.get("correlations", [])[:3],
        timestamp=datetime.now().isoformat()
    )
    workflow_graph.add_edge(dataset_node_id, node_id, action="profiled")
    return node_id

def log_question(question: str, answer: str):
    _session_questions.append({
        "question": question,
        "answer": answer,
        "time": datetime.now().strftime("%H:%M")
    })

def generate_session_summary() -> str:
    if not _session_questions:
        return "No questions asked in this session."
    qa_text = "\n".join([
        f"Q: {item['question']}\nA: {item['answer']}"
        for item in _session_questions
    ])
    prompt = f"""
Summarize this analyst's data exploration session in very concisely.
Cover: what they investigated, key insights, implied next steps.

SESSION Q&A:
{qa_text}

SUMMARY:
"""
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

def add_summary_node(parent_node_id: str) -> dict:
    if not _session_questions:
        return {"error": "No questions to summarize yet"}

    summary = generate_session_summary()
    date_label = datetime.now().strftime("%Y-%m-%d")
    node_id = _new_id("summary")

    # embed the summary — stored for comparison later, no Gemini
    embedding = embedding_model.encode(summary).tolist()

    workflow_graph.add_node(node_id,
        type="session_summary",
        date=date_label,
        summary=summary,
        questions_count=len(_session_questions),
        timestamp=datetime.now().isoformat()
    )
    workflow_graph.add_edge(parent_node_id, node_id, action="summarized")

    # store embedding separately (networkx nodes don't handle numpy well)
    _summary_store[node_id] = {
        "date": date_label,
        "summary": summary,
        "embedding": embedding
    }

    questions_summarized = len(_session_questions)
    _session_questions.clear()

    return {
        "node_id": node_id,
        "date": date_label,
        "summary": summary,
        "questions_summarized": questions_summarized
    }

def compare_sessions(node_id_a: str, node_id_b: str) -> dict:
    """
    Pure embedding comparison — zero LLM calls.
    Uses cosine similarity + sentence-level semantic drift detection.
    """
    if node_id_a not in _summary_store or node_id_b not in _summary_store:
        return {"error": "One or both session nodes not found"}

    a = _summary_store[node_id_a]
    b = _summary_store[node_id_b]

    vec_a = np.array(a["embedding"]).reshape(1, -1)
    vec_b = np.array(b["embedding"]).reshape(1, -1)

    # overall session similarity
    overall_similarity = float(cosine_similarity(vec_a, vec_b)[0][0])

    if overall_similarity > 0.85:
        similarity_label = "Very similar sessions — analyst revisited same topics"
    elif overall_similarity > 0.65:
        similarity_label = "Moderately similar — some overlap with new directions"
    elif overall_similarity > 0.4:
        similarity_label = "Different focus — analysis shifted significantly"
    else:
        similarity_label = "Completely different sessions — unrelated analysis"

    # sentence level drift — find what's new in B vs A
    sentences_b = [s.strip() for s in b["summary"].split(".") if s.strip()]
    sentences_a = [s.strip() for s in a["summary"].split(".") if s.strip()]

    if sentences_b and sentences_a:
        vecs_b = embedding_model.encode(sentences_b)
        vecs_a = embedding_model.encode(sentences_a)

        # for each sentence in B, find its max similarity to any sentence in A
        drift_scores = []
        for i, vec in enumerate(vecs_b):
            sims = cosine_similarity([vec], vecs_a)[0]
            max_sim = float(np.max(sims))
            drift_scores.append({
                "sentence": sentences_b[i],
                "max_similarity_to_A": round(max_sim, 3),
                "is_new": max_sim < 0.5  # below 0.5 = genuinely new topic
            })

        new_in_b = [d["sentence"] for d in drift_scores if d["is_new"]]
        retained = [d["sentence"] for d in drift_scores if not d["is_new"]]
    else:
        new_in_b = []
        retained = []
        drift_scores = []

    return {
        "session_a": {"node_id": node_id_a, "date": a["date"]},
        "session_b": {"node_id": node_id_b, "date": b["date"]},
        "overall_similarity": round(overall_similarity, 3),
        "similarity_label": similarity_label,
        "new_focus_in_session_b": new_in_b,
        "retained_from_session_a": retained,
        "sentence_level_drift": drift_scores
    }

def get_all_summary_nodes() -> list:
    return [
        {"node_id": k, "date": v["date"], "summary": v["summary"]}
        for k, v in _summary_store.items()
    ]

def get_last_node_id() -> str | None:
    if not workflow_graph.nodes:
        return None
    return list(workflow_graph.nodes)[-1]

def get_graph_state() -> dict:
    nodes = []
    for node_id, data in workflow_graph.nodes(data=True):
        nodes.append({"id": node_id, **data})
    edges = []
    for src, dst, data in workflow_graph.edges(data=True):
        edges.append({"from": src, "to": dst, **data})
    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }
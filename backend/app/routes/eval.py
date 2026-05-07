from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.eval import evaluate_retrieval, evaluate_hallucination
from app.services.llm import ask_about_dataset
from app.services.graph import get_graph_state, workflow_graph, log_question
from app.routes.upload import get_active_profile

router = APIRouter()

class EvalRequest(BaseModel):
    question: str

@router.post("/eval/query")
async def eval_query(request: EvalRequest):
    """
    Runs a question through the full pipeline and returns
    both the answer AND quality metrics.
    """
    profile = get_active_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Upload a dataset first")

    graph_state = get_graph_state() if workflow_graph.nodes else None
    result = ask_about_dataset(request.question, profile, graph_state)
    log_question(request.question, result["answer"])

    # eval 1 — retrieval quality
    retrieval_eval = evaluate_retrieval(
        request.question,
        result["retrieved_sections"],
        result["context_used"]
    )

    # eval 2 — hallucination check on answer
    hallucination_eval = evaluate_hallucination(
        result["answer"],
        profile.get("columns", [])
    )

    return JSONResponse(content={
        "question": request.question,
        "answer": result["answer"],
        "eval": {
            "retrieval": retrieval_eval,
            "hallucination": hallucination_eval,
            "graph_nodes_used": len(result.get("graph_nodes_used", []))
        }
    })


@router.get("/eval/session")
async def eval_session():
    """
    Session-level health report — how well has the system
    been retrieving across all questions asked.
    """
    from app.services.embeddings import _profile_chunks
    profile = get_active_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Upload a dataset first")

    graph_data = get_graph_state()
    summary_nodes = [n for n in graph_data["nodes"] if n["type"] == "session_summary"]
    profiling_nodes = [n for n in graph_data["nodes"] if n["type"] == "profiling"]

    return JSONResponse(content={
        "session_health": {
            "total_graph_nodes": graph_data["total_nodes"],
            "datasets_analyzed": len([n for n in graph_data["nodes"] if n["type"] == "dataset"]),
            "sessions_summarized": len(summary_nodes),
            "profile_chunks_indexed": len(_profile_chunks),
            "columns_indexed": len(profile.get("columns", [])),
        },
        "data_quality_snapshot": {
            "missing_columns": list(profile.get("missing", {}).keys()),
            "skewed_columns": list(profile.get("skewness", {}).keys()),
            "outlier_columns": list(profile.get("outliers", {}).keys()),
            "top_correlations": profile.get("correlations", [])[:3]
        },
        "sessions": [
            {
                "node_id": n["node_id"] if "node_id" in n else n["id"],
                "date": n.get("date"),
                "questions_count": n.get("questions_count", 0),
                "summary_preview": n.get("summary", "")[:100]
            }
            for n in summary_nodes
        ]
    })
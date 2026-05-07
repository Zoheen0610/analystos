from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.llm import ask_about_dataset
from app.services.graph import log_question, get_graph_state
from app.routes.upload import get_active_profile

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
async def chat(request: ChatRequest):
    profile = get_active_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Upload a dataset first")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    graph_state = get_graph_state()
    result = ask_about_dataset(request.question, profile, graph_state)
    log_question(request.question, result["answer"])

    return JSONResponse(content={
        "question": request.question,
        "answer": result["answer"],
        "retrieval_metadata": result["retrieved_sections"],
        "graph_nodes_used": result["graph_nodes_used"],
        "context_used": result["context_used"]
    })
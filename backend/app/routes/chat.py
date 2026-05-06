from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.llm import ask_about_dataset
from app.services.graph import log_question
from app.routes.upload import _stored_profile

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
async def chat(request: ChatRequest):
    if not _stored_profile:
        raise HTTPException(status_code=404, detail="Upload a dataset first")

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = ask_about_dataset(request.question, _stored_profile)
    log_question(request.question, result["answer"])

    return JSONResponse(content={
        "question": request.question,
        "answer": result["answer"],
        "retrieval_metadata": result["retrieved_sections"],
        "context_used": result["context_used"]
    })
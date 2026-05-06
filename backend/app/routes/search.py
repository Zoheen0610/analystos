from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.embeddings import search_columns

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/search/columns")
async def semantic_search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = search_columns(request.query, request.top_k)
    
    if not results:
        raise HTTPException(status_code=404, detail="No columns indexed yet. Upload a dataset first.")
    
    return JSONResponse(content={
        "query": request.query,
        "results": results
    })
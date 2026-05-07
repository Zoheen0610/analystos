from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services.codegen import generate_suggestions, generate_preprocessing_code
from app.routes.upload import get_active_profile

router = APIRouter()

@router.post("/preprocess/full")
async def full_preprocessing_pipeline():
    profile = get_active_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Upload a dataset first")
    suggestions = generate_suggestions(profile)
    code_result = generate_preprocessing_code(profile, suggestions)

    return JSONResponse(content={
        "step_1_suggestions": suggestions,
        "step_2_code": code_result["code"],
        "hallucination_check": code_result["hallucination_check"],
        "warning": (
            f"Invented columns: {code_result['hallucination_check']['invented_columns']}"
            if not code_result["hallucination_check"]["passed"] else None
        )
    })
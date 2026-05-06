from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services.codegen import generate_suggestions, generate_preprocessing_code
from app.routes.upload import _stored_profile

router = APIRouter()

@router.post("/preprocess/full")
async def full_preprocessing_pipeline():
    if not _stored_profile:
        raise HTTPException(status_code=404, detail="Upload a dataset first")

    suggestions = generate_suggestions(_stored_profile)
    code_result = generate_preprocessing_code(_stored_profile, suggestions)

    return JSONResponse(content={
        "step_1_suggestions": suggestions,
        "step_2_code": code_result["code"],
        "hallucination_check": code_result["hallucination_check"],
        "warning": (
            f"Invented columns: {code_result['hallucination_check']['invented_columns']}"
            if not code_result["hallucination_check"]["passed"] else None
        )
    })
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
from app.services.profiler import profile_dataset
from app.services.graph import add_dataset_node, add_profiling_node
from app.services.embeddings import build_column_index, build_profile_chunks

router = APIRouter()

_stored_profile = {}
_last_profiling_node = {"id": None}

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

    profile = profile_dataset(df)
    profile["filename"] = file.filename
    _stored_profile.update(profile)

    # build both indexes on upload
    build_column_index(profile["columns"])
    build_profile_chunks(profile)         # new — chunks for RAG

    dataset_node = add_dataset_node(file.filename, profile["shape"])
    profiling_node = add_profiling_node(dataset_node, profile)
    _last_profiling_node["id"] = profiling_node

    return JSONResponse(content={
        "message": "Dataset uploaded and profiled successfully",
        "profile": profile,
        "graph": {
            "dataset_node": dataset_node,
            "profiling_node": profiling_node
        }
    })

@router.get("/profile")
async def get_profile():
    if not _stored_profile:
        raise HTTPException(status_code=404, detail="No dataset uploaded yet")
    return JSONResponse(content={"profile": _stored_profile})
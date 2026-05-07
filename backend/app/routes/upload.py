from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
import pandas as pd
import io
from app.services.profiler import profile_dataset
from app.services.graph import add_dataset_node, add_profiling_node
from app.services.embeddings import build_column_index, build_profile_chunks

router = APIRouter()

# keyed by filename instead of single dict
_profiles: dict[str, dict] = {}
_active_file: dict[str, str] = {"filename": None}  # tracks which file chat/search uses


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

    # store by filename — doesn't overwrite others
    _profiles[file.filename] = profile

    # newly uploaded file becomes active
    _active_file["filename"] = file.filename

    # build indexes for this file
    build_column_index(profile["columns"])
    build_profile_chunks(profile)

    dataset_node = add_dataset_node(file.filename, profile["shape"])
    profiling_node = add_profiling_node(dataset_node, profile)

    return JSONResponse(content={
        "message": f"{file.filename} uploaded and profiled",
        "active_file": file.filename,
        "total_files": len(_profiles),
        "profile": profile,
        "graph": {
            "dataset_node": dataset_node,
            "profiling_node": profiling_node
        }
    })


@router.get("/profile")
async def get_profile(filename: str = Query(None)):
    if not _profiles:
        raise HTTPException(status_code=404, detail="No datasets uploaded yet")

    # return specific file or active file
    target = filename or _active_file["filename"]
    if target not in _profiles:
        raise HTTPException(status_code=404, detail=f"{target} not found. Available: {list(_profiles.keys())}")

    return JSONResponse(content={"profile": _profiles[target]})


@router.post("/switch")
async def switch_active_file(filename: str = Query(...)):
    """Switch which file chat and search operate on."""
    if filename not in _profiles:
        raise HTTPException(
            status_code=404,
            detail=f"File not found. Available: {list(_profiles.keys())}"
        )

    _active_file["filename"] = filename

    # rebuild indexes for the switched file
    build_column_index(_profiles[filename]["columns"])
    build_profile_chunks(_profiles[filename])

    return JSONResponse(content={
        "message": f"Switched active file to {filename}",
        "active_file": filename
    })


@router.get("/files")
async def list_files():
    """List all uploaded files and which is active."""
    if not _profiles:
        raise HTTPException(status_code=404, detail="No files uploaded yet")
    return JSONResponse(content={
        "active_file": _active_file["filename"],
        "files": [
            {
                "filename": name,
                "rows": p["shape"]["rows"],
                "columns": p["shape"]["columns"],
                "is_active": name == _active_file["filename"]
            }
            for name, p in _profiles.items()
        ]
    })


def get_active_profile() -> dict:
    """Used by chat/preprocess to get current active profile."""
    name = _active_file["filename"]
    if not name or name not in _profiles:
        return {}
    return _profiles[name]
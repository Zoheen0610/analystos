from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.chat import router as chat_router
from app.routes.graph import router as graph_router
from app.routes.search import router as search_router
from app.routes.preprocess import router as preprocess_router
# from app.services.graph import load_graph_memory
from app.routes.eval import router as eval_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AnalystOS Lite", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load_graph_memory()

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(graph_router)
app.include_router(search_router)
app.include_router(preprocess_router)
app.include_router(eval_router)

@app.get("/")
def root():
    return {"message": "AnalystOS Lite running"}
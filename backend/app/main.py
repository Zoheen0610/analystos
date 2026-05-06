from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.chat import router as chat_router
from app.routes.graph import router as graph_router
from app.routes.search import router as search_router
from app.routes.preprocess import router as preprocess_router
# from app.services.graph import load_graph_memory

app = FastAPI(title="AnalystOS Lite", version="1.0.0")

# load_graph_memory()

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(graph_router)
app.include_router(search_router)
app.include_router(preprocess_router)

@app.get("/")
def root():
    return {"message": "AnalystOS Lite running"}
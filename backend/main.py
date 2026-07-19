from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, knowledge, rag_admin, translate, literature

app = FastAPI(
    title="Awadhi Language Assistant API",
    description="Phase 1: knowledge-base-backed chat + district selector + proverbs/words lookup.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(rag_admin.router)
app.include_router(translate.router)
app.include_router(literature.router)


@app.get("/health")
def health():
    return {"status": "ok", "phase": 1}

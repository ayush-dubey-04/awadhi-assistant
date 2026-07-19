"""
Small admin surface for the RAG layer — checking whether the Chroma
collection is populated, and triggering ingestion manually. Not wired into
app startup automatically: ingestion requires Ollama's embedding model to be
running, and failing hard on startup because of an optional feature would be
a worse failure mode than just telling you to run it yourself.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/status")
def rag_status():
    try:
        from rag.chroma_client import collection_size
        return {"collection_populated": True, "item_count": collection_size()}
    except Exception as e:
        return {"collection_populated": False, "item_count": 0, "error": str(e)}


@router.post("/ingest")
def trigger_ingest():
    try:
        from rag.ingest import ingest_all
        return ingest_all()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ingestion failed — is Ollama running with the embedding model pulled? ({e})",
        )

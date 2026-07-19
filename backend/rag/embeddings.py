"""
Embedding function for ChromaDB, backed by Ollama's /api/embeddings endpoint.

WHY OLLAMA FOR EMBEDDINGS INSTEAD OF THE OBVIOUS CHOICES:
- ChromaDB's default embedding function downloads a MiniLM ONNX model from an
  S3 bucket at first use.
- sentence-transformers models download from huggingface.co.
Both require network access this project's dev/CI environment may not have,
and both add a second model runtime alongside Ollama. Since you're already
running Ollama for chat (Phase 2), using it for embeddings too means one
runtime, one thing to keep running, one thing to document.

Trade-off you should know about: Ollama's embedding models are not
Awadhi-aware either (same low-resource-language problem as chat generation).
Semantic search here will cluster on general Hindi/Devanagari or English
semantic similarity, not on Awadhi-specific meaning. It will still meaningfully
outperform exact keyword matching for near-miss phrasing, spelling variants,
and paraphrases — that's the actual win, not "understands Awadhi dialect."

Recommended model: `ollama pull nomic-embed-text` (274MB, decent multilingual
performance, fast on CPU).
"""
import os
import httpx
from chromadb import EmbeddingFunction, Documents, Embeddings

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Implements Chroma's EmbeddingFunction protocol (a callable taking a
    list of documents and returning a list of embedding vectors)."""

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            for text in input:
                resp = client.post(
                    f"{OLLAMA_HOST}/api/embeddings",
                    json={"model": EMBEDDING_MODEL, "prompt": text},
                )
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
        return embeddings

    def name(self) -> str:
        return f"ollama-{EMBEDDING_MODEL}"

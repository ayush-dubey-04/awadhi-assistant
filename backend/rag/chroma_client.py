"""
ChromaDB persistence layer. One collection holds both words and proverbs
from the knowledge base, disambiguated by a 'type' metadata field, so a
single semantic query can surface either.
"""
import os
import chromadb
from rag.embeddings import OllamaEmbeddingFunction

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "awadhi_knowledge"

_client = None
_collection = None


def get_collection():
    """Lazily initializes the persistent Chroma client and collection.
    Lazy on purpose: importing this module shouldn't require Ollama to be
    running — only actually using the collection should."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=OllamaEmbeddingFunction(),
        )
    return _collection


def collection_size() -> int:
    return get_collection().count()

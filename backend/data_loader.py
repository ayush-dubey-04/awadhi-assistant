"""
Loads the JSON knowledge base once and keeps it in memory.
This is intentionally file-based for Phase 1. Phase 2/3 will replace this
with PostgreSQL (structured data) + ChromaDB (embeddings for RAG retrieval) —
see README "Migration path" section.
"""
import json
from pathlib import Path
from functools import lru_cache

DATA_PATH = Path(__file__).parent / "data" / "knowledge_base.json"


@lru_cache(maxsize=1)
def load_knowledge_base() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_words(district: str | None = None) -> list[dict]:
    kb = load_knowledge_base()
    words = kb["words"]
    if district and district != "General Awadh":
        words = [w for w in words if w["district"] in (district, "General Awadh")]
    return words


def get_proverbs(district: str | None = None) -> list[dict]:
    kb = load_knowledge_base()
    proverbs = kb["proverbs"]
    if district and district != "General Awadh":
        proverbs = [p for p in proverbs if p["district"] in (district, "General Awadh")]
    return proverbs


def get_literature() -> list[dict]:
    """Literature verses aren't district-tagged — Ramcharitmanas isn't
    specific to one district, unlike vocabulary/proverbs."""
    kb = load_knowledge_base()
    return kb.get("literature", [])


def get_literature_by_id(verse_id: str) -> dict | None:
    for v in get_literature():
        if v["id"] == verse_id:
            return v
    return None


def get_entry_by_id(entry_id: str) -> dict | None:
    """Looks up a full word, proverb, or literature record by its ID. Used by
    RAG retrieval to hydrate Chroma's (id, metadata) results back into full
    KB entries — Chroma stores embeddings + metadata, not the full record."""
    kb = load_knowledge_base()
    for w in kb["words"]:
        if w["id"] == entry_id:
            return {**w, "_type": "word"}
    for p in kb["proverbs"]:
        if p["id"] == entry_id:
            return {**p, "_type": "proverb"}
    for v in kb.get("literature", []):
        if v["id"] == entry_id:
            return {**v, "_type": "literature"}
    return None


def get_districts() -> list[str]:
    kb = load_knowledge_base()
    return kb["_meta"]["districts"]

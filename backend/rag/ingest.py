"""
Ingests words + proverbs from the JSON knowledge base into ChromaDB.

Idempotent via upsert — safe to re-run after editing knowledge_base.json;
existing IDs get their embeddings/metadata refreshed rather than duplicated.

Run directly to (re)populate the collection:
    python -m rag.ingest
"""
from data_loader import load_knowledge_base
from rag.chroma_client import get_collection


def _word_document(w: dict) -> str:
    # The embedded text determines what semantic search actually matches on.
    # Including Hindi and English glosses means a query in either language
    # can retrieve the Awadhi term, not just exact Awadhi text.
    return f"{w['awadhi']} | Hindi: {w['hindi']} | English: {w['english']} | {w.get('notes', '')}"


def _proverb_document(p: dict) -> str:
    return f"{p['awadhi']} | Hindi: {p['hindi']} | English: {p['english']} | Meaning: {p['meaning']} | {p['usage_context']}"


def _literature_document(v: dict) -> str:
    return (
        f"{v['source_text']} | Transliteration: {v['transliteration']} | "
        f"Hindi: {v['hindi_meaning']} | English: {v['english_meaning']} | "
        f"Context: {v['context']}"
    )


def ingest_all() -> dict:
    kb = load_knowledge_base()
    collection = get_collection()

    ids, documents, metadatas = [], [], []

    for w in kb["words"]:
        ids.append(w["id"])
        documents.append(_word_document(w))
        metadatas.append({"type": "word", "district": w["district"]})

    for p in kb["proverbs"]:
        ids.append(p["id"])
        documents.append(_proverb_document(p))
        metadatas.append({"type": "proverb", "district": p["district"]})

    for v in kb.get("literature", []):
        ids.append(v["id"])
        documents.append(_literature_document(v))
        # Literature isn't district-tagged; use a sentinel so it's always
        # included regardless of which district filter a query applies.
        metadatas.append({"type": "literature", "district": "General Awadh"})

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return {"ingested": len(ids), "collection_count": collection.count()}


if __name__ == "__main__":
    result = ingest_all()
    print(f"Ingested {result['ingested']} entries. Collection now has {result['collection_count']} items.")

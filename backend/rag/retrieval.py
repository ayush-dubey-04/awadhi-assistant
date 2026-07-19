"""
Semantic search over the Chroma collection, with optional district filtering.
This is what makes RAG meaningfully better than Phase 2's static "first N
entries for this district" grounding: instead of always grounding with the
same handful of words, we ground with whatever's actually semantically close
to what the user asked.
"""
from rag.chroma_client import get_collection
from data_loader import get_entry_by_id

DEFAULT_TOP_K = 4
# Chroma returns cosine distance (0 = identical, larger = less similar) for
# the default space. This isn't a calibrated probability — it's a relative
# ranking signal. Don't present it to users as a percentage confidence score.
DISTANCE_THRESHOLD = 1.0


def semantic_search(query: str, district: str | None = None, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    collection = get_collection()

    where = None
    if district and district != "General Awadh":
        where = {"$or": [{"district": district}, {"district": "General Awadh"}]}

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where,
    )

    hydrated = []
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for entry_id, distance in zip(ids, distances):
        if distance > DISTANCE_THRESHOLD:
            continue
        entry = get_entry_by_id(entry_id)
        if entry:
            hydrated.append({**entry, "_distance": distance})

    return hydrated

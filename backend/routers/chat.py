"""
Phase 1 chat logic: no LLM involved yet (that's Phase 2).
This is a transparent keyword-lookup responder against the knowledge base.
It exists so the frontend, API contract, and UX flow are all working end-to-end
before we introduce the much harder problem of LLM-generated Awadhi text.
"""
import re
from fastapi import APIRouter
from models import ChatRequest, ChatResponse, MatchedEntry
from data_loader import get_words, get_proverbs
from prompts import build_system_prompt, build_system_prompt_from_entries
import llm_client
from rag.retrieval import semantic_search

router = APIRouter(prefix="/chat", tags=["chat"])

GREETINGS = {"namaste", "namaskar", "hello", "hi", "raam raam", "ram ram", "प्रणाम", "नमस्ते"}

# Words too common/short to be useful match signals (would false-positive on almost anything)
STOPWORDS = {"a", "an", "the", "to", "of", "in", "is", "it", "or", "on", "as", "at", "by", "be"}

# Below this Chroma cosine-distance, treat a semantic match as confident
# enough to answer directly from the KB instead of routing to the LLM.
# UNCALIBRATED — this number was chosen without a real embedding model
# available to test against (see README Phase 3 section). Tune it against
# real nomic-embed-text distances once you have Ollama embeddings running;
# don't trust this default blindly.
STRONG_SEMANTIC_MATCH_DISTANCE = 0.35


def _tokenize(text: str) -> set[str]:
    """Whole-word, lowercase tokens only. No substring matching — substring
    matching previously matched 'xyzabc' to a proverb because 'a' is a
    substring of it. Caught by smoke testing, fixed here."""
    tokens = re.findall(r"[a-zA-Z\u0900-\u097F]+", text.lower())
    return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}


def _find_matches(message: str, district: str) -> list[MatchedEntry]:
    msg_tokens = _tokenize(message)
    matches: list[MatchedEntry] = []

    if not msg_tokens:
        return matches

    for w in get_words(district):
        entry_tokens = _tokenize(w["awadhi"]) | _tokenize(w["hindi"]) | _tokenize(w["english"])
        if msg_tokens & entry_tokens:
            matches.append(MatchedEntry(
                type="word", id=w["id"], awadhi=w["awadhi"], hindi=w["hindi"],
                english=w["english"], district=w["district"], extra=w.get("notes"),
            ))

    for p in get_proverbs(district):
        entry_tokens = _tokenize(p["awadhi"]) | _tokenize(p["hindi"]) | _tokenize(p["english"])
        if msg_tokens & entry_tokens:
            matches.append(MatchedEntry(
                type="proverb", id=p["id"], awadhi=p["awadhi"], hindi=p["hindi"],
                english=p["english"], district=p["district"],
                extra=f"{p['meaning']} | Usage: {p['usage_context']}",
            ))

    return matches


def _entry_to_matched(entry: dict) -> MatchedEntry:
    if entry["_type"] == "word":
        return MatchedEntry(
            type="word", id=entry["id"], awadhi=entry["awadhi"], hindi=entry["hindi"],
            english=entry["english"], district=entry["district"], extra=entry.get("notes"),
        )
    return MatchedEntry(
        type="proverb", id=entry["id"], awadhi=entry["awadhi"], hindi=entry["hindi"],
        english=entry["english"], district=entry["district"],
        extra=f"{entry['meaning']} | Usage: {entry['usage_context']}",
    )


@router.get("/model-status")
async def model_status():
    return await llm_client.check_status()


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    msg_lower = req.message.strip().lower()

    if msg_lower in GREETINGS:
        return ChatResponse(
            reply=f"राम राम! ({req.district} की बोली में स्वागत है) — Ram Ram! Welcome, greeting in {req.district} style.",
            district=req.district,
            matched_entries=[],
            source="knowledge_base_lookup",
        )

    matches = _find_matches(req.message, req.district)

    # Verified knowledge base always wins over LLM generation — it's the one
    # source in this system we've actually vetted.
    if matches:
        top = matches[0]
        if top.type == "word":
            reply = f"'{top.awadhi}' ({top.district}) means '{top.english}' in English / '{top.hindi}' in Hindi."
        else:
            reply = f"That relates to the proverb: '{top.awadhi}' — {top.english}. {top.extra}"
        return ChatResponse(reply=reply, district=req.district, matched_entries=matches,
                             source="knowledge_base_lookup")

    # Tier 2: no exact match. Try semantic search (Phase 3) so near-miss
    # phrasing, spelling variants, or paraphrases can still find a real KB
    # entry instead of immediately falling to the LLM. If Chroma/Ollama
    # embeddings aren't available, this degrades to an empty list rather
    # than failing the request — RAG is an enhancement, not a hard dependency.
    rag_entries: list[dict] = []
    try:
        rag_entries = semantic_search(req.message, req.district)
    except Exception:
        rag_entries = []

    if rag_entries and rag_entries[0]["_distance"] <= STRONG_SEMANTIC_MATCH_DISTANCE:
        top = rag_entries[0]
        matched = _entry_to_matched(top)
        if matched.type == "word":
            reply = f"'{matched.awadhi}' ({matched.district}) means '{matched.english}' in English / '{matched.hindi}' in Hindi."
        else:
            reply = f"That's close to the proverb: '{matched.awadhi}' — {matched.english}. {matched.extra}"
        return ChatResponse(
            reply=reply, district=req.district, matched_entries=[matched],
            source="knowledge_base_semantic_match",
            caveat=(
                f"Matched by semantic similarity, not exact wording (distance={top['_distance']:.2f}). "
                "Still verified knowledge-base content, just fuzzy-matched to your phrasing."
            ),
        )

    # Tier 3 — no exact or confident semantic match. Fall back to LLM,
    # grounded with whatever RAG retrieved (better than Phase 2's static
    # first-N-of-district), or static grounding if RAG found nothing/failed.
    try:
        if rag_entries:
            system_prompt = build_system_prompt_from_entries(req.district, rag_entries)
        else:
            system_prompt = build_system_prompt(req.district)
        llm_reply = await llm_client.generate_chat_reply(system_prompt, req.message)
        return ChatResponse(
            reply=llm_reply,
            district=req.district,
            matched_entries=[],
            source="llm_generated",
            caveat=(
                "Generated by an LLM with minimal real Awadhi training data. "
                "Not verified — treat vocabulary and grammar with skepticism until "
                "a native speaker reviews it."
            ),
        )
    except llm_client.LLMUnavailableError:
        return ChatResponse(
            reply=(
                "मोय ई शब्द अबहीं नाहीं मालूम — no knowledge-base match, and the LLM backend "
                "isn't reachable. Start Ollama with 'ollama serve' and make sure the model is "
                "pulled to get generated replies for unmatched queries."
            ),
            district=req.district,
            matched_entries=[],
            source="llm_unavailable",
        )
    except llm_client.LLMModelNotFoundError as e:
        return ChatResponse(
            reply=f"No knowledge-base match, and the LLM model isn't available: {e}",
            district=req.district,
            matched_entries=[],
            source="llm_unavailable",
        )

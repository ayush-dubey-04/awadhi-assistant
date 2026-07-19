"""
Literature module.

Two tiers, same trust philosophy as chat.py:
1. If the user's text closely matches one of our verified, cross-checked
   verses, return the verified explanation directly.
2. Otherwise, fall back to an LLM explanation grounded with RAG-retrieved
   verses for context, clearly marked as unverified.

The verified seed set is intentionally tiny (2 verses) — see README. This
module's honest value right now is the tier-1 lookup and the pattern for
adding more verified verses; the LLM tier is a stopgap, not the point.
"""
from fastapi import APIRouter
from typing import List
from models import LiteratureVerse, ExplainRequest, ExplainResponse
from data_loader import get_literature
from prompts import build_literature_explain_prompt
import llm_client
from rag.retrieval import semantic_search

router = APIRouter(prefix="/literature", tags=["literature"])

STRONG_VERSE_MATCH_DISTANCE = 0.35  # same caveat as chat.py — uncalibrated, tune with real embeddings


@router.get("/verses", response_model=List[LiteratureVerse])
def list_verses():
    return get_literature()


@router.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    try:
        results = semantic_search(req.text, district=None, top_k=3)
    except Exception:
        results = []

    literature_results = [r for r in results if r.get("_type") == "literature"]

    if literature_results and literature_results[0]["_distance"] <= STRONG_VERSE_MATCH_DISTANCE:
        top = literature_results[0]
        verse = LiteratureVerse(
            id=top["id"], source_text=top["source_text"], transliteration=top["transliteration"],
            work=top["work"], kanda=top["kanda"], hindi_meaning=top["hindi_meaning"],
            english_meaning=top["english_meaning"], context=top["context"],
            verification_note=top.get("verification_note"),
        )
        return ExplainResponse(
            explanation=f"{verse.english_meaning} ({verse.hindi_meaning})",
            matched_verse=verse,
            source="verified_verse_match",
        )

    try:
        prompt = build_literature_explain_prompt(literature_results)
        llm_reply = await llm_client.generate_chat_reply(prompt, req.text)
        return ExplainResponse(
            explanation=llm_reply,
            matched_verse=None,
            source="llm_generated",
            caveat=(
                "No verified verse matched closely. This explanation is LLM best-effort, "
                "grounded with whatever related verified verses were found, but not itself "
                "verified. Misattribution risk is real for literary/religious texts — verify "
                "against a scholarly source before treating this as authoritative."
            ),
        )
    except llm_client.LLMUnavailableError:
        return ExplainResponse(
            explanation="No verified verse matched, and the LLM backend isn't reachable.",
            matched_verse=None,
            source="llm_unavailable",
        )
    except llm_client.LLMModelNotFoundError as e:
        return ExplainResponse(
            explanation=f"No verified verse matched, and the LLM model isn't available: {e}",
            matched_verse=None,
            source="llm_unavailable",
        )

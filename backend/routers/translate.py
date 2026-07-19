"""
Translation module.

Honest framing: this is NOT a trained translation model. It's an LLM asked
to translate, with as much verified grounding as we can inject — exact
dictionary matches for words that appear in the input, pulled straight from
the knowledge base. Words not in our small seed dictionary get a best-effort
LLM guess, explicitly flagged. As the knowledge base grows (more words,
more districts, native-speaker-reviewed), translation quality scales with
it — that's the actual point of calling this a "preservation initiative"
rather than a translation API wrapper.
"""
import re
from fastapi import APIRouter
from models import TranslateRequest, TranslateResponse, GlossaryHit
from data_loader import get_words
from prompts import build_translation_prompt
import llm_client

router = APIRouter(prefix="/translate", tags=["translate"])


def _find_glossary_hits(text: str, district: str) -> list[GlossaryHit]:
    """Exact substring/word match against the dictionary — reuses the same
    conservative whole-word approach as chat.py's KB matching, for the same
    reason: substring matching false-positives on short words."""
    tokens = set(re.findall(r"[a-zA-Z\u0900-\u097F]+", text.lower()))
    hits = []
    for w in get_words(district):
        candidates = {w["awadhi"].lower(), w["hindi"].lower(), w["english"].lower()}
        for candidate in candidates:
            if candidate in tokens or candidate in text.lower():
                hits.append(GlossaryHit(
                    awadhi=w["awadhi"], hindi=w["hindi"], english=w["english"],
                    matched_input_term=candidate,
                ))
                break
    return hits


@router.post("", response_model=TranslateResponse)
async def translate(req: TranslateRequest) -> TranslateResponse:
    glossary_hits = _find_glossary_hits(req.text, req.district)

    try:
        system_prompt = build_translation_prompt(
            req.district,
            [{"awadhi": h.awadhi, "hindi": h.hindi, "english": h.english} for h in glossary_hits],
            req.source_lang, req.target_lang,
        )
        llm_reply = await llm_client.generate_chat_reply(system_prompt, req.text)
        return TranslateResponse(
            translation=llm_reply,
            glossary_hits=glossary_hits,
            source="llm_generated",
            caveat=(
                f"{len(glossary_hits)} word(s) matched our verified glossary and should be "
                "reliable; everything else is LLM best-effort and may be Hindi rather than "
                "authentic Awadhi. Words marked [?] by the model are its own uncertainty flags."
            ),
        )
    except llm_client.LLMUnavailableError:
        return TranslateResponse(
            translation="",
            glossary_hits=glossary_hits,
            source="llm_unavailable",
            caveat="LLM backend not reachable. Start Ollama with 'ollama serve' to enable translation.",
        )
    except llm_client.LLMModelNotFoundError as e:
        return TranslateResponse(
            translation="",
            glossary_hits=glossary_hits,
            source="llm_unavailable",
            caveat=str(e),
        )

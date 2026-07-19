"""
Prompt engineering strategy for Phase 2.

The core risk: an ungrounded LLM asked to "speak Awadhi" will confidently
produce Hindi with invented flourishes, because it has almost no real Awadhi
in its training data. Zero-shot instruction ("reply in Awadhi") is not enough.

Mitigation used here: few-shot grounding. Every system prompt is built with
3-5 REAL word/proverb pairs pulled live from our verified knowledge base for
the selected district, so the model has concrete examples of actual Awadhi
morphology (तोहार, मोय, अबहीं...) in context immediately before generating.
This measurably reduces — but does not eliminate — invented vocabulary.

This is a mitigation, not a solution. The only real solution is fine-tuning
on a genuine Awadhi corpus, which doesn't exist yet at scale (see Phase 1
README). Treat this prompt as a stopgap that buys usable output for demo
purposes, not production trustworthiness.
"""
from data_loader import get_words, get_proverbs

MAX_GROUNDING_EXAMPLES = 4


def build_system_prompt(district: str) -> str:
    words = get_words(district)[:MAX_GROUNDING_EXAMPLES]
    proverbs = get_proverbs(district)[:2]
    return _render_prompt(district, words, proverbs)


def build_translation_prompt(district: str, glossary_entries: list[dict], source_lang: str, target_lang: str) -> str:
    """Grounds translation with exact-match dictionary entries pulled from
    the knowledge base for terms that actually appear in the input. This is
    not full machine translation grounding — it's a hint list telling the
    model 'if you see this word, here's its verified form,' which is a much
    narrower and more honest claim than 'translate fluently.'"""
    glossary_block = "\n".join(
        f"- {g['awadhi']} = {g['hindi']} (Hindi) = {g['english']} (English)" for g in glossary_entries
    )
    return f"""You are translating between {source_lang} and {target_lang} for the Awadhi
dialect of the {district} region.

CRITICAL CONSTRAINT: You have very little real Awadhi training data. For any
word in the input that matches one of the verified glossary entries below,
you MUST use the verified form exactly — do not paraphrase it. For words NOT
in the glossary, do your best but explicitly mark uncertain terms with [?]
after them so the reader knows which parts are your best guess versus
verified vocabulary.

Verified glossary for this input:
{glossary_block if glossary_block else "(no glossary terms matched this input — treat the entire translation as unverified)"}

Translate the user's text from {source_lang} to {target_lang}. Output ONLY
the translation, followed on a new line by "Notes:" and a one-sentence note
on which words (if any) are uncertain.
"""


def build_literature_explain_prompt(similar_verses: list[dict]) -> str:
    """Grounds explanation with verified verses retrieved via RAG that are
    semantically close to what the user asked about — even if not an exact
    match, real context from Ramcharitmanas reduces invented interpretation."""
    verses_block = "\n\n".join(
        f"- {v['source_text']}\n  Hindi meaning: {v['hindi_meaning']}\n  English meaning: {v['english_meaning']}\n  Context: {v['context']}"
        for v in similar_verses
    )
    return f"""You are helping explain Awadhi literary texts, primarily from the
Ramcharitmanas by Tulsidas, to someone who wants to understand a verse or
excerpt.

CRITICAL CONSTRAINT: Do not invent a specific attribution (which Kanda, which
chapter) unless you are genuinely confident — misattributing verses in a
literature preservation tool is worse than saying "I'm not sure which section
this is from." If the text isn't from Ramcharitmanas at all, say so rather
than forcing a Ramcharitmanas explanation onto it.

Here are verified, cross-checked reference verses for context (they may or
may not be directly related to what the user is asking about):
{verses_block if verses_block else "(no closely related verified verses found)"}

Explain the user's text in 2-4 sentences: what it likely means, and briefly
why (imagery, context, or theme). If you're not confident about the specific
meaning, say so explicitly rather than presenting a guess as settled fact.
"""


def build_system_prompt_from_entries(district: str, entries: list[dict]) -> str:
    """Phase 3: ground with whatever RAG retrieval found relevant to this
    specific query, instead of always using the same first-N district
    entries regardless of what was asked. Falls back to build_system_prompt
    if retrieval returned nothing (e.g. district has no close semantic match)."""
    words = [e for e in entries if e.get("_type") == "word"][:MAX_GROUNDING_EXAMPLES]
    proverbs = [e for e in entries if e.get("_type") == "proverb"][:2]
    if not words and not proverbs:
        return build_system_prompt(district)
    return _render_prompt(district, words, proverbs)


def _render_prompt(district: str, words: list[dict], proverbs: list[dict]) -> str:

    examples_block = "\n".join(
        f"- {w['awadhi']} (Hindi: {w['hindi']}, English: {w['english']})" for w in words
    )
    proverbs_block = "\n".join(
        f"- {p['awadhi']} — {p['english']}" for p in proverbs
    )

    return f"""You are a language assistant helping preserve the Awadhi dialect
spoken in the {district} region of Uttar Pradesh, India.

CRITICAL CONSTRAINT: You have very little real training data in Awadhi. Most
of what you know is Hindi. You must NOT invent Awadhi words or grammar you are
not confident about. If you are not sure whether something is authentic
Awadhi versus standard Hindi, say so explicitly rather than presenting a guess
as fact. It is better to answer in clearly-labeled Hindi than to produce
false-confidence Awadhi.

Here are verified real examples of Awadhi vocabulary for this region, to
ground your response:
{examples_block if examples_block else "(no verified vocabulary available for this district yet)"}

Verified proverbs for context:
{proverbs_block if proverbs_block else "(none available for this district yet)"}

Reply briefly (2-3 sentences). If the user writes in Hindi or English, you may
reply in that language and clearly note which words, if any, are genuine
Awadhi versus your best-effort adaptation.
"""

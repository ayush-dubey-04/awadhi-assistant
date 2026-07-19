"""
Pydantic schemas shared across the API.
Kept in one module for Phase 1 since the surface area is small;
split into models/ package once we add translation + literature models in Phase 4.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's chat message, any script/language")
    district: str = Field(default="General Awadh", description="Selected district for dialect context")


class MatchedEntry(BaseModel):
    type: str  # "word" | "proverb"
    id: str
    awadhi: str
    hindi: str
    english: str
    district: str
    extra: Optional[str] = None  # notes for words, meaning+usage for proverbs


class ChatResponse(BaseModel):
    reply: str
    district: str
    matched_entries: List[MatchedEntry] = []
    source: str = "knowledge_base_lookup"  # "knowledge_base_lookup" | "llm_generated" | "llm_unavailable"
    caveat: Optional[str] = None  # set when reply is LLM-generated and unverified


class WordEntry(BaseModel):
    id: str
    awadhi: str
    hindi: str
    english: str
    district: str
    notes: Optional[str] = None


class ProverbEntry(BaseModel):
    id: str
    awadhi: str
    hindi: str
    english: str
    district: str
    meaning: str
    usage_context: str


class LiteratureVerse(BaseModel):
    id: str
    source_text: str
    transliteration: str
    work: str
    kanda: str
    hindi_meaning: str
    english_meaning: str
    context: str
    verification_note: Optional[str] = None


class ExplainRequest(BaseModel):
    text: str = Field(..., min_length=1, description="A verse or excerpt to explain")


class ExplainResponse(BaseModel):
    explanation: str
    matched_verse: Optional[LiteratureVerse] = None
    source: str  # "verified_verse_match" | "llm_generated" | "llm_unavailable"
    caveat: Optional[str] = None


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_lang: str = Field(..., description="'awadhi' | 'hindi' | 'english'")
    target_lang: str = Field(..., description="'awadhi' | 'hindi' | 'english'")
    district: str = Field(default="General Awadh")


class GlossaryHit(BaseModel):
    awadhi: str
    hindi: str
    english: str
    matched_input_term: str


class TranslateResponse(BaseModel):
    translation: str
    glossary_hits: List[GlossaryHit] = []
    source: str  # "llm_generated" | "llm_unavailable"
    caveat: Optional[str] = None

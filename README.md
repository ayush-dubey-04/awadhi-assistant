# Awadhi Language Assistant — Phase 1 Prototype

## What this actually is (read this first)

This is **not** a fluent Awadhi-speaking chatbot. It's a working, tested pipeline:
React chat UI → FastAPI → JSON knowledge base lookup, with a district selector
that filters results. There is no LLM in Phase 1. When you type something that
matches a word or proverb in the seed dataset, you get a real answer pulled
from that entry. When you type something that isn't in the dataset, you get an
honest "I don't know that yet" — not a hallucinated guess.

That's deliberate. The point of Phase 1 is to prove the plumbing works and
give you a UI to build on, before we touch the much harder problem (Phase 2+)
of getting an LLM to actually produce fluent Awadhi, which no open model can
currently do out of the box — see the earlier discussion in this project about
Awadhi being a low-resource language with no large training corpus.

## Seed data caveat

`backend/data/knowledge_base.json` contains ~9 illustrative entries (5 words,
4 proverbs). These are widely-published, commonly-cited Awadh-belt proverbs —
**they have not been verified against native speakers per district** and the
district tagging for some entries is a reasonable guess, not fieldwork. Do not
treat this as an authoritative source. Replacing this file with reviewed,
sourced, native-speaker-verified content is the actual preservation work —
everything else in this repo is just the container for it.

## Architecture (Phase 1)

```
React (Vite) ──HTTP/JSON──▶ FastAPI ──▶ knowledge_base.json (in-memory, cached)
```

## Folder structure

```
awadhi-assistant/
├── backend/
│   ├── main.py              # FastAPI app, CORS, router registration
│   ├── models.py            # Pydantic request/response schemas
│   ├── data_loader.py       # Loads + caches the JSON knowledge base
│   ├── llm_client.py        # Ollama HTTP client (Phase 2)
│   ├── prompts.py           # KB-grounded system prompt builder (Phase 2/3)
│   ├── requirements.txt
│   ├── data/
│   │   └── knowledge_base.json
│   ├── rag/                 # Phase 3
│   │   ├── embeddings.py    # Ollama-backed Chroma embedding function
│   │   ├── chroma_client.py # Persistent Chroma client/collection
│   │   ├── ingest.py        # Loads knowledge_base.json into Chroma
│   │   └── retrieval.py     # Semantic search with district filtering
│   └── routers/
│       ├── chat.py          # POST /chat — 3-tier: exact → semantic → LLM
│       ├── knowledge.py     # GET /knowledge/words, /proverbs, /districts
│       ├── rag_admin.py     # GET /rag/status, POST /rag/ingest
│       ├── translate.py     # POST /translate — glossary-grounded translation
│       └── literature.py    # GET /literature/verses, POST /literature/explain
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── index.css
│       └── components/
│           ├── DistrictSelector.jsx
│           ├── ChatWindow.jsx
│           └── MessageBubble.jsx
└── README.md
```

## Running it

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs on `http://127.0.0.1:8000`. Check `http://127.0.0.1:8000/docs` for the
interactive Swagger UI — useful for testing endpoints without the frontend.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://127.0.0.1:5173` and expects the backend at port 8000
(configurable via `VITE_API_BASE` env var).

## What I tested before handing this to you

- `/health`, `/knowledge/districts`, `/knowledge/proverbs?district=X` — all return correct data.
- `/chat` with a known word (Devanagari and via English gloss) — matches correctly.
- `/chat` with a known proverb keyword — matches correctly.
- `/chat` with gibberish input — **initially returned a false-positive match**
  due to a substring-matching bug (single-letter words like "a" matched
  almost anything). Fixed by switching to whole-word tokenized matching with
  a stopword list. Re-tested and confirmed gibberish now correctly returns
  "no match."
- `npm run build` completes with no errors.

I did not test on mobile viewport widths or with a screen reader — worth
doing before you show this to anyone outside your own dev loop.

## Migration path (why the code is structured this way)

- `data_loader.py` isolates all knowledge-base access behind functions
  (`get_words`, `get_proverbs`, `get_districts`). In Phase 3 this gets
  swapped for PostgreSQL queries + ChromaDB retrieval without touching the
  routers.
- `models.py` centralizes schemas so Phase 4 (translation, literature) can
  add new models without restructuring existing ones.
- The chat router's `source` field in the response (`"knowledge_base_lookup"`)
  is there so the frontend — and you — can always tell whether a reply came
  from the verified seed data or, later, from an LLM. Keep this field alive
  through every phase. Users of a preservation tool deserve to know whether
  they're reading something verified or something generated.

## Suggested git commits for this phase

```bash
git init
git add backend/
git commit -m "Phase 1: FastAPI backend with knowledge-base lookup chat + district filtering"

git add frontend/
git commit -m "Phase 1: React chat UI with district selector"

git add README.md .gitignore
git commit -m "Phase 1: docs and project scaffolding"
```

Add a `.gitignore` (included) before your first commit so you don't check in
`node_modules/`, `venv/`, or `__pycache__/`.

**Phase 2 commits:**
```bash
git add backend/llm_client.py backend/prompts.py backend/routers/chat.py backend/models.py backend/requirements.txt
git commit -m "Phase 2: Ollama LLM fallback with KB-grounded prompting and honest source labeling"

git add frontend/src/
git commit -m "Phase 2: surface verified-vs-generated distinction and live model status in UI"
```

**Phase 3 commits:**
```bash
git add backend/rag/ backend/routers/rag_admin.py
git commit -m "Phase 3: ChromaDB RAG layer with Ollama-backed embeddings"

git add backend/routers/chat.py backend/prompts.py backend/data_loader.py backend/main.py backend/requirements.txt
git commit -m "Phase 3: three-tier chat routing — exact match, semantic match, grounded LLM fallback"
```

**Phase 4 commits:**
```bash
git add backend/data/knowledge_base.json backend/data_loader.py backend/rag/ingest.py backend/models.py backend/prompts.py
git commit -m "Phase 4: literature verses + translation glossary data model, RAG ingestion, prompts"

git add backend/routers/translate.py backend/routers/literature.py backend/main.py
git commit -m "Phase 4: translation and literature explain endpoints"

git add frontend/src/
git commit -m "Phase 4: Translate and Literature tabs in the UI"
```

## Phase 2 — Ollama + Gemma/Qwen fallback

### What changed

`/chat` now works in two tiers:
1. **Knowledge base match** (same as Phase 1) — always wins, always trusted,
   `source: "knowledge_base_lookup"`.
2. **No match** → falls back to a local LLM via Ollama, grounded with real
   examples from the knowledge base for that district (see `prompts.py`),
   `source: "llm_generated"` with a `caveat` field the frontend renders as a
   visible unverified-content warning.

If Ollama isn't running or the model isn't pulled, you get an honest
`source: "llm_unavailable"` message telling you what to do — never a crash,
never a silent wrong answer.

### Set realistic expectations before you run this

Gemma and Qwen have essentially no real Awadhi in their training data (see
the corpus scarcity research cited earlier in this project). What you'll get
from the LLM tier is fluent-sounding **Hindi**, occasionally dressed with a
genuine Awadhi word pulled from the grounding examples, not authentic Awadhi
grammar. The system prompt in `prompts.py` explicitly tells the model to
flag uncertainty rather than invent — models don't reliably follow that
instruction, so verify output yourself before trusting it. This is why every
LLM-generated reply carries a visible caveat in the UI. Don't remove that
caveat to make demos look more polished than the system actually is.

### Setup

```bash
# install Ollama: https://ollama.com/download
ollama serve                 # in one terminal, if not already running as a service
ollama pull gemma2:9b        # or: ollama pull qwen2.5:7b
```

Configure the backend via environment variables (defaults shown):
```bash
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=gemma2:9b     # must match what you pulled
export OLLAMA_TIMEOUT_SECONDS=30
```

Restart the backend after pulling a model — `GET /chat/model-status` (also
shown live in the frontend header) tells you whether Ollama is reachable and
whether the configured model is actually installed.

### What I tested for this phase (and what I couldn't)

I don't have network access to ollama.com or its model registry in my build
environment, so **I could not pull a real model or verify actual Awadhi
output quality** — that test is yours to run. What I did verify, against a
disposable mock server that mimics Ollama's real `/api/tags` and `/api/chat`
response shapes:
- `GET /chat/model-status` correctly reports reachable/unreachable and
  installed models.
- `POST /chat` correctly routes to the LLM only when there's no KB match.
- The system prompt sent to the LLM actually contains real grounding
  examples from the knowledge base (confirmed via the mock echoing back
  whether "तोहार" appeared in the system message).
- `source` and `caveat` fields are set correctly for the LLM path.
- With no Ollama process running at all, the whole request degrades to a
  clear message instead of a 500 error or a hang.

When you run this against a real model, watch specifically for: does it
actually use the grounded Awadhi words, or default to Hindi and ignore them?
That's the real signal for whether this approach is worth continuing into
Phase 3, versus needing actual fine-tuning data first.

## Phase 3 — RAG with ChromaDB

### What changed

`/chat` is now a three-tier pipeline:
1. **Exact keyword match** (Phase 1) — always wins, `source: "knowledge_base_lookup"`.
2. **Semantic search match** (new) — if no exact match, Chroma does a
   similarity search over the knowledge base. If the closest result is
   confidently close (distance ≤ `STRONG_SEMANTIC_MATCH_DISTANCE` in
   `routers/chat.py`), it's returned directly as
   `source: "knowledge_base_semantic_match"` — still verified content, just
   matched by meaning instead of exact wording.
3. **LLM fallback** (Phase 2, improved) — if nothing matched confidently,
   generate with the LLM, but now grounded with whatever RAG actually
   retrieved for *this specific query* instead of Phase 2's static
   first-N-words-for-the-district. `source: "llm_generated"` as before.

Every tier degrades independently and explicitly:
- Chroma/embeddings unreachable → RAG tier silently returns nothing, chat
  proceeds using exact match + static Phase 2 grounding. Verified with
  Ollama fully stopped — confirmed no crash, no hang, correct `503` from
  `/rag/ingest`, correct `llm_unavailable` from `/chat`.
- Chroma reachable but collection empty → same graceful no-op.

### Why Ollama for embeddings, not sentence-transformers

ChromaDB's default embedder downloads from an S3 bucket; sentence-transformers
downloads from huggingface.co. Both were unreachable from my build sandbox,
and more importantly, both add a second model runtime you'd have to keep
alive alongside Ollama. `rag/embeddings.py` implements Chroma's
`EmbeddingFunction` protocol as a thin wrapper around Ollama's own
`/api/embeddings` endpoint — one runtime, one thing to document, one thing to
keep running.

**Trade-off:** Ollama's embedding models have the same low-resource-language
gap as chat generation. Semantic search here clusters on general
Hindi/English/Devanagari meaning, not Awadhi-specific nuance. It's still a
real improvement over exact-token matching for paraphrases and near-miss
phrasing — that's the actual, honest value here, not "understands dialect."

### Setup

```bash
ollama pull nomic-embed-text     # ~274MB, in addition to your chat model
```

Populate the vector store (idempotent — safe to re-run after editing
`knowledge_base.json`):
```bash
curl -X POST http://127.0.0.1:8000/rag/ingest
# or: python -m rag.ingest   (from inside backend/)
```

Check it worked: `GET /rag/status` returns `item_count` — should be 9 after
ingesting the seed data.

### What I tested for this phase (and what I couldn't)

Same constraint as Phase 2: no network path to a real embedding model from my
sandbox. What I verified with a disposable mock Ollama server that returns
deterministic hash-based fake vectors (proves plumbing, not semantic
quality):
- `POST /rag/ingest` populates all 9 entries into Chroma; `GET /rag/status`
  correctly reports the count.
- Querying with the *exact* text of an already-ingested document returns
  that document at distance `0.0` — proves storage, retrieval, and distance
  scoring work correctly end to end.
- Querying with unrelated gibberish returns zero results after threshold
  filtering — proves the distance filter in `retrieval.py` actually filters.
- The LLM-fallback tier correctly receives RAG-retrieved context in its
  grounding prompt (confirmed via the mock echoing which KB terms appeared
  in the system message).
- Full graceful degradation with Ollama completely stopped: `/rag/ingest`
  returns a clean `503` with an actionable message, `/chat` still serves
  exact KB matches perfectly and returns `llm_unavailable` for anything else
  — no crash anywhere in the chain.

**What I could not verify, and this is the important one:** whether
`STRONG_SEMANTIC_MATCH_DISTANCE = 0.35` is remotely the right threshold for
real embeddings. It's an uncalibrated guess. Fake hash-based vectors don't
tell you anything about where real semantic near-misses actually land in
distance space. Once you have `nomic-embed-text` running, deliberately query
with paraphrases of things in the knowledge base (not exact text) and look at
the actual distances that come back — then tune that constant to match. Don't
trust the current number in a demo you're showing to someone else.

## Phase 4 — Translation and literature modules

### What changed

**Translation** (`POST /translate`): exact-match glossary lookup against the
knowledge base for any word in the input, injected into the LLM prompt as a
mandatory-use glossary. Words not in the (tiny, 5-entry) dictionary get an
LLM best-effort guess, which the prompt instructs the model to flag with
`[?]`. Response includes `glossary_hits` so the frontend can show exactly
which words were verified versus generated — same trust-labeling pattern as
chat and literature.

**Literature** (`GET /literature/verses`, `POST /literature/explain`): two
verified Ramcharitmanas chaupais, cross-checked against multiple published
sources before inclusion (see `verification_note` on each entry — I did not
rely on memory alone for centuries-old verse text, given how bad a wrong
verse would be in a tool whose whole premise is preservation). `/explain`
matches user input against these verified verses first; only falls to
LLM-grounded explanation if nothing matches, and the prompt explicitly
instructs the model not to guess at attribution (which Kanda/chapter) if
unsure — misattributing scripture is a worse failure than admitting
uncertainty.

The frontend now has three tabs — Chat, Translate, Literature — sharing the
same district selector and the same visible verified/unverified distinction
throughout.

### What I tested for this phase (and what I couldn't)

- `knowledge_base.json` literature entries: validated as well-formed JSON;
  both verses cross-checked against multiple independent published sources
  via web search before inclusion (see search results referenced in this
  project's conversation) — not just recalled from memory.
- `/literature/verses` returns both seed verses correctly.
- `/literature/explain` with the exact stored verse text returns
  `verified_verse_match` with the correct verse.
- `/literature/explain` with unrelated text correctly falls to the LLM tier,
  grounded with RAG-retrieved literature context (verified via mock server).
- `/translate` correctly detects glossary hits (e.g. "your" → तोहार) and
  passes them to the LLM prompt as mandatory-use terms.
- Both endpoints degrade cleanly with Ollama fully stopped — confirmed
  `llm_unavailable` responses, no crashes, no hangs.
- `npm run build` succeeds with the new Translate/Literature tabs.

**Not tested, same standing caveat as Phases 2-3:** real translation quality
and real literature-explanation quality from an actual model. The mock
server proves the pipeline wiring, not whether Gemma/Qwen will actually
produce something useful here. Given everything established across this
project about Awadhi being low-resource, my honest expectation is that
translation quality will be the weakest of all four features — full sentence
translation requires far more linguistic competence than word lookup or
single-verse explanation. If you only have bandwidth to seriously vet one
module with a native speaker before showing this to anyone, make it
translation, not literature or chat.

### Seed data status after Phase 4

- 5 words, 4 proverbs, 2 verified literature verses. Still nowhere near
  enough for any of the four features to be trustworthy standalone — every
  phase of this project has been infrastructure, not corpus. The corpus is
  still the actual unsolved problem stated all the way back in the original
  scoping conversation.

## Known limitations (not bugs, just Phase 1 scope)

- No stemming — "sow" matches, "sowing" doesn't. Fine for a lookup demo, not
  fine for production.
- No transliteration table — typing "tohar" in Latin script won't match the
  Devanagari entry "तोहार". Real users will type in both scripts constantly;
  this needs solving before Phase 2, not after.
- No persistence — knowledge base is a static file, no way to add entries
  without editing JSON by hand. Fine for now, becomes the Postgres job in
  Phase 3.

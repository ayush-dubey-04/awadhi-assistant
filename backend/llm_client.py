"""
Thin async client for a local Ollama server (https://ollama.com).

Deliberately isolated from the router logic so:
1. It can be swapped for a different local/remote LLM backend later without
   touching chat.py.
2. It can be mocked in tests without needing a real model loaded.

IMPORTANT — read before assuming this "speaks Awadhi":
Gemma and Qwen were not trained on meaningful amounts of Awadhi text. Expect
fluent-sounding Hindi with occasional Awadhi vocabulary, not authentic Awadhi
grammar. The system prompt below grounds the model with real examples from
our knowledge base to push it toward using verified Awadhi words rather than
inventing them, but this is a mitigation, not a fix. Treat every LLM-generated
reply as unverified until a native speaker reviews it — the API response
carries a `source` and `caveat` field specifically so the frontend never
presents generated text as equivalent to the verified knowledge base.
"""
import os
import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:9b")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))


class LLMUnavailableError(Exception):
    """Raised when Ollama isn't running or isn't reachable at OLLAMA_HOST."""
    pass


class LLMModelNotFoundError(Exception):
    """Raised when Ollama is reachable but the configured model isn't pulled."""
    pass


async def check_status() -> dict:
    """Ping Ollama and report whether the configured model is available.
    Used by GET /chat/model-status so the frontend can show a real state
    instead of silently failing on first chat message."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {
                "ollama_reachable": True,
                "configured_model": OLLAMA_MODEL,
                "model_available": any(OLLAMA_MODEL in m for m in models),
                "installed_models": models,
            }
    except (httpx.ConnectError, httpx.TimeoutException):
        return {
            "ollama_reachable": False,
            "configured_model": OLLAMA_MODEL,
            "model_available": False,
            "installed_models": [],
        }


async def generate_chat_reply(system_prompt: str, user_message: str) -> str:
    """Calls Ollama's /api/chat with a system + user message, non-streaming.
    Raises LLMUnavailableError if Ollama isn't running, LLMModelNotFoundError
    if the model isn't pulled — callers must handle both and degrade gracefully
    rather than crashing the request."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise LLMUnavailableError(
            f"Could not reach Ollama at {OLLAMA_HOST}. Is 'ollama serve' running?"
        ) from e

    if resp.status_code == 404:
        raise LLMModelNotFoundError(
            f"Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}"
        )
    resp.raise_for_status()

    data = resp.json()
    return data["message"]["content"]

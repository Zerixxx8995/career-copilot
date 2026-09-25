"""
Gemini LLM client wrapper — uses the new google-genai SDK (google.genai).
Supports plain text generation and tool-calling via generate_content.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import google.genai as genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level client (single instance)
_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


CANDIDATE_MODELS = [
    settings.LLM_MODEL,
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-flash-lite-latest",
]


async def _generate_content_with_fallback(
    client: genai.Client,
    contents: list,
    config: Optional[types.GenerateContentConfig] = None,
) -> Any:
    seen = set()
    models = [m for m in CANDIDATE_MODELS if not (m in seen or seen.add(m))]
    last_exc = None
    for m in models:
        try:
            kwargs: Dict[str, Any] = {"model": m, "contents": contents}
            if config:
                kwargs["config"] = config
            return await client.aio.models.generate_content(**kwargs)
        except Exception as exc:
            last_exc = exc
            logger.warning("Gemini model '%s' failed (%s), trying fallback model...", m, exc)
    raise last_exc


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_text(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Generate plain text from a prompt (no tool-calling)."""
    client = get_client()
    contents = []
    if system_prompt:
        contents.append(types.Content(role="user", parts=[types.Part(text=system_prompt + "\n\n" + prompt)]))
    else:
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

    response = await _generate_content_with_fallback(client, contents)
    return response.text or ""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Any],
    system_prompt: Optional[str] = None,
) -> Any:
    """
    Run one round of tool-calling with the Gemini model.
    Returns the raw response so the orchestrator can inspect function_calls.
    """
    client = get_client()

    config_kwargs: Dict[str, Any] = {}
    if tools:
        config_kwargs["tools"] = tools
    if system_prompt:
        config_kwargs["system_instruction"] = system_prompt

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    # Convert messages to Content objects
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        parts = msg.get("parts", [])
        if isinstance(parts, list):
            converted_parts = []
            for p in parts:
                if isinstance(p, str):
                    converted_parts.append(types.Part(text=p))
                else:
                    converted_parts.append(p)
            contents.append(types.Content(role=role, parts=converted_parts))

    response = await _generate_content_with_fallback(client, contents, config)
    logger.debug("LLM tool response candidates: %d", len(response.candidates or []))
    return response

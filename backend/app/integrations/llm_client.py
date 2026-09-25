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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_text(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Generate plain text from a prompt (no tool-calling)."""
    client = get_client()
    contents = []
    if system_prompt:
        contents.append(types.Content(role="user", parts=[types.Part(text=system_prompt + "\n\n" + prompt)]))
    else:
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

    response = await client.aio.models.generate_content(
        model=settings.LLM_MODEL,
        contents=contents,
    )
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

    kwargs: Dict[str, Any] = {
        "model": settings.LLM_MODEL,
        "contents": contents,
    }
    if config:
        kwargs["config"] = config

    response = await client.aio.models.generate_content(**kwargs)
    logger.debug("LLM tool response candidates: %d", len(response.candidates or []))
    return response

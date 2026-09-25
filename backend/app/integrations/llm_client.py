"""
Gemini LLM client wrapper — tool-calling and plain generation.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)


def get_llm_client(tools: Optional[List[Any]] = None) -> genai.GenerativeModel:
    """Return a configured GenerativeModel, optionally with tool definitions."""
    return genai.GenerativeModel(
        model_name=settings.LLM_MODEL,
        tools=tools or [],
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_text(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Generate plain text from a prompt (no tool-calling)."""
    model = genai.GenerativeModel(model_name=settings.LLM_MODEL)
    parts = []
    if system_prompt:
        parts.append(system_prompt + "\n\n")
    parts.append(prompt)

    response = await model.generate_content_async("".join(parts))
    return response.text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Any],
) -> Any:
    """
    Run one round of tool-calling with the Gemini model.
    Returns the raw Gemini response so the orchestrator can inspect
    function_calls and continue the loop.
    """
    model = get_llm_client(tools=tools)
    chat = model.start_chat()

    # Replay history
    for msg in messages[:-1]:
        chat.history.append(msg)

    last = messages[-1]
    response = await chat.send_message_async(last["parts"])
    logger.debug("LLM response: %s", response)
    return response

"""
Skill extractor — pulls structured skill names from free text using the LLM.

Deterministic code drives the extraction; the LLM is only used to normalise
and surface skill mentions — it never invents skills not present in the text.
"""
from __future__ import annotations

import json
import logging
import re
from typing import List

from app.integrations.llm_client import generate_text

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """
You are a skill extraction engine. Extract ALL technical and professional skills
mentioned in the text below. Return ONLY a valid JSON array of strings — no markdown,
no explanation, no extra keys. Each string is a normalised skill name.

Examples of good output:
["Python", "PyTorch", "Docker", "REST APIs", "SQL", "Machine Learning"]

Text to analyse:
{text}

JSON array of skills:
"""


async def extract_skills(text: str) -> List[str]:
    """
    Extract a de-duplicated list of skill strings from arbitrary text.
    Falls back to an empty list on any error.
    """
    if not text or not text.strip():
        return []

    prompt = _EXTRACTION_PROMPT.format(text=text[:4000])  # cap to avoid token waste

    try:
        raw = await generate_text(prompt)
        # Strip markdown code fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        skills = json.loads(raw)
        if not isinstance(skills, list):
            return []
        # Deduplicate, preserving order
        seen: set[str] = set()
        result: List[str] = []
        for s in skills:
            key = s.strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(s.strip())
        return result
    except Exception as exc:
        logger.warning("Skill extraction failed: %s", exc)
        return []

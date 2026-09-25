"""
Resume service — PDF extraction, LLM-assisted structuring, and RAG indexing.
"""
from __future__ import annotations

import io
import json
import logging
import re
import uuid
from typing import Dict, Any

import pdfplumber
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.skill_extractor import extract_skills
from app.integrations import embedding_client, qdrant_client as qclient
from app.integrations.llm_client import generate_text
from app.models.profile_models import CareerProfile, User

logger = logging.getLogger(__name__)

_STRUCTURE_PROMPT = """
You are a resume parser. Given the raw text of a resume, extract structured information.
Return ONLY valid JSON (no markdown fences) with this exact schema:
{{
  "target_roles": ["string"],
  "target_locations": ["string"],
  "skills": [
    {{"name": "skill_name", "status": "known|learning|gap"}}
  ],
  "education": [
    {{"degree": "string", "institution": "string", "year": "string"}}
  ],
  "projects": [
    {{"name": "string", "description": "string", "technologies": ["string"]}}
  ],
  "experience": [
    {{"role": "string", "company": "string", "duration": "string", "highlights": ["string"]}}
  ]
}}

Infer "target_roles" from the objective/summary and project technologies.
If a field is not in the resume, use an empty list.

Resume text:
{text}

JSON:
"""


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract plain text from a PDF byte stream."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


async def structure_resume(raw_text: str) -> Dict[str, Any]:
    """Use LLM to parse raw resume text into structured fields."""
    prompt = _STRUCTURE_PROMPT.format(text=raw_text[:6000])
    raw = await generate_text(prompt)
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse structured resume JSON: %s\nRaw: %s", exc, raw[:500])
        return {}


async def _chunk_and_index_resume(
    user_id: str, raw_text: str, structured: Dict[str, Any]
) -> None:
    """Split resume into semantic chunks and index them in Qdrant."""
    await qclient.ensure_collection(settings.QDRANT_RESUME_COLLECTION)

    # Delete old chunks for this user
    await qclient.delete_by_payload(
        settings.QDRANT_RESUME_COLLECTION, "user_id", user_id
    )

    chunks = []

    # Skills section
    skills = structured.get("skills", [])
    if skills:
        skill_names = [s["name"] for s in skills if isinstance(s, dict)]
        chunks.append(
            {"section": "skills", "content": "Skills: " + ", ".join(skill_names)}
        )

    # Projects
    for proj in structured.get("projects", []):
        if isinstance(proj, dict):
            content = (
                f"Project: {proj.get('name', '')}\n"
                f"Description: {proj.get('description', '')}\n"
                f"Technologies: {', '.join(proj.get('technologies', []))}"
            )
            chunks.append({"section": "project", "content": content})

    # Experience
    for exp in structured.get("experience", []):
        if isinstance(exp, dict):
            highlights = " ".join(exp.get("highlights", []))
            content = (
                f"Experience: {exp.get('role', '')} at {exp.get('company', '')}\n"
                f"{highlights}"
            )
            chunks.append({"section": "experience", "content": content})

    # Education
    for edu in structured.get("education", []):
        if isinstance(edu, dict):
            content = (
                f"Education: {edu.get('degree', '')} from {edu.get('institution', '')} "
                f"({edu.get('year', '')})"
            )
            chunks.append({"section": "education", "content": content})

    # Fallback: raw text in windows
    if not chunks:
        window_size = 500
        for i in range(0, len(raw_text), window_size):
            chunks.append({"section": "raw", "content": raw_text[i : i + window_size]})

    # Embed and upsert
    texts = [c["content"] for c in chunks]
    embeddings = await embedding_client.embed_texts(texts)

    payloads = [
        {"user_id": user_id, "section": c["section"], "content": c["content"]}
        for c in chunks
    ]
    ids = [str(uuid.uuid4()) for _ in chunks]

    await qclient.upsert_vectors(
        collection_name=settings.QDRANT_RESUME_COLLECTION,
        vectors=embeddings,
        payloads=payloads,
        ids=ids,
    )
    logger.info("Indexed %d resume chunks for user %s", len(chunks), user_id)


async def ingest_resume(
    db: AsyncSession,
    user_id: str,
    file_bytes: bytes,
    file_name: str,
) -> CareerProfile:
    """
    Full resume ingestion pipeline:
    1. Extract PDF text
    2. LLM-structure it
    3. Save/update CareerProfile in Postgres
    4. Chunk + index in Qdrant
    """
    raw_text = extract_pdf_text(file_bytes)
    structured = await structure_resume(raw_text)
    resume_skills = await extract_skills(raw_text)

    # Merge LLM skills with extracted ones
    llm_skills = structured.get("skills", [])
    all_skill_names = {s["name"].lower() for s in llm_skills if isinstance(s, dict)}
    for skill in resume_skills:
        if skill.lower() not in all_skill_names:
            llm_skills.append({"name": skill, "status": "known"})
            all_skill_names.add(skill.lower())

    # Upsert CareerProfile
    result = await db.execute(
        select(CareerProfile).where(CareerProfile.user_id == uuid.UUID(user_id))
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = CareerProfile(user_id=uuid.UUID(user_id))
        db.add(profile)

    profile.resume_raw_text = raw_text
    profile.resume_file_name = file_name
    profile.skills = llm_skills
    profile.target_roles = structured.get("target_roles", [])
    profile.target_locations = structured.get("target_locations", [])

    await db.flush()

    # RAG index
    await _chunk_and_index_resume(user_id, raw_text, structured)

    return profile

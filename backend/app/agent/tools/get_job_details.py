"""
get_job_details tool — full job retrieval + lazy RAG indexing on first access.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.integrations import embedding_client, qdrant_client as qclient
from app.models.job_models import JobPosting

logger = logging.getLogger(__name__)


async def get_job_details(
    db: AsyncSession,
    job_id: str,
) -> Dict[str, Any]:
    """
    Retrieve full job details and trigger RAG indexing if not already indexed.

    Input:  { job_id: string }
    Output: { job_id, title, company, location, role_category, full_description, requirements }
    """
    result = await db.execute(
        select(JobPosting).where(JobPosting.id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    # Lazy RAG indexing
    if not job.rag_indexed:
        await _index_job(job)
        job.rag_indexed = True
        await db.flush()

    return {
        "job_id": str(job.id),
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "role_category": job.role_category,
        "full_description": job.full_description,
        "requirements": job.requirements or [],
    }


async def _index_job(job: JobPosting) -> None:
    """Chunk the job posting and index in Qdrant."""
    await qclient.ensure_collection(settings.QDRANT_JOB_COLLECTION)

    chunks = []

    # Requirements chunk
    if job.requirements:
        chunks.append({
            "content": "Requirements: " + "; ".join(job.requirements),
            "job_id": str(job.id),
            "section": "requirements",
        })

    # Description window chunks (500-char windows)
    desc = job.full_description
    window = 500
    for i in range(0, len(desc), window):
        chunks.append({
            "content": desc[i : i + window],
            "job_id": str(job.id),
            "section": "description",
        })

    if not chunks:
        return

    texts = [c["content"] for c in chunks]
    embeddings = await embedding_client.embed_texts(texts)
    ids = [str(uuid.uuid4()) for _ in chunks]

    await qclient.upsert_vectors(
        collection_name=settings.QDRANT_JOB_COLLECTION,
        vectors=embeddings,
        payloads=chunks,
        ids=ids,
    )
    logger.info("Indexed %d chunks for job %s", len(chunks), job.id)

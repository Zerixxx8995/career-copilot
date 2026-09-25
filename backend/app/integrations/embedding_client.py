"""
Embedding client — uses google-genai SDK (google.genai) for text-embedding-004.
"""
from __future__ import annotations

import logging
from typing import List

import google.genai as genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.integrations.llm_client import get_client

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def embed_text(text: str) -> List[float]:
    """Return a single embedding vector for `text` (document mode)."""
    client = get_client()
    result = await client.aio.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=[types.Content(role="user", parts=[types.Part(text=text)])],
    )
    # result.embeddings is a list of ContentEmbedding objects
    return list(result.embeddings[0].values)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def embed_query(text: str) -> List[float]:
    """Return an embedding optimised for query/search."""
    return await embed_text(text)


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch embed a list of texts (sequential — rate-limit safe)."""
    embeddings = []
    for text in texts:
        emb = await embed_text(text)
        embeddings.append(emb)
    return embeddings

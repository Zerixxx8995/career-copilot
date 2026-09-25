"""
Qdrant vector database client — collection management, upsert, and search.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncQdrantClient] = None


def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
    return _client


async def ensure_collection(collection_name: str, vector_size: int = settings.EMBEDDING_DIMENSION) -> None:
    """Create the collection if it doesn't exist."""
    client = get_qdrant_client()
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if collection_name not in names:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection: %s", collection_name)


async def upsert_vectors(
    collection_name: str,
    vectors: List[List[float]],
    payloads: List[Dict[str, Any]],
    ids: Optional[List[str]] = None,
) -> None:
    """Upsert points into a collection."""
    client = get_qdrant_client()
    if ids is None:
        ids = [str(uuid.uuid4()) for _ in vectors]

    points = [
        qmodels.PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i])
        for i in range(len(vectors))
    ]
    await client.upsert(collection_name=collection_name, points=points)
    logger.debug("Upserted %d vectors into '%s'", len(points), collection_name)


async def search_vectors(
    collection_name: str,
    query_vector: List[float],
    limit: int = 5,
    filter_conditions: Optional[qmodels.Filter] = None,
) -> List[qmodels.ScoredPoint]:
    """Semantic search — returns top-k scored points."""
    client = get_qdrant_client()
    results = await client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        query_filter=filter_conditions,
        with_payload=True,
    )
    return results


async def delete_by_payload(collection_name: str, field: str, value: str) -> None:
    """Delete all points where payload[field] == value."""
    client = get_qdrant_client()
    try:
        await client.delete(
            collection_name=collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(key=field, match=qmodels.MatchValue(value=value))]
                )
            ),
        )
    except Exception as exc:
        logger.warning("Qdrant delete_by_payload skipped/failed for %s=%s: %s", field, value, exc)

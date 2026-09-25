"""
Agent controller — validates query, runs the agent, shapes response.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.agent.orchestrator import run_agent
from sqlalchemy.ext.asyncio import AsyncSession


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000, description="Natural-language query")


async def handle_agent_query(
    db: AsyncSession,
    user_id: str,
    request: AgentQueryRequest,
) -> dict:
    result = await run_agent(db=db, user_id=user_id, query=request.query)
    return {
        "trace_id": result["trace_id"],
        "answer": result["final_answer"],
        "steps_count": len(result["steps"]),
    }


async def handle_get_trace(
    db: AsyncSession,
    user_id: str,
    trace_id: str,
) -> dict:
    import uuid
    from sqlalchemy import select
    from app.models.trace_models import AgentTrace

    result = await db.execute(
        select(AgentTrace).where(
            AgentTrace.trace_id == uuid.UUID(trace_id),
            AgentTrace.user_id == uuid.UUID(user_id),
        )
    )
    trace = result.scalar_one_or_none()
    if trace is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")

    return {
        "trace_id": str(trace.trace_id),
        "user_query": trace.user_query,
        "steps": trace.steps,
        "final_answer": trace.final_answer,
        "created_at": trace.created_at.isoformat(),
    }

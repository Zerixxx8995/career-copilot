"""Agent router — URL mapping only."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.agent_controller import (
    AgentQueryRequest,
    handle_agent_query,
    handle_get_trace,
)
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/query", summary="Submit a natural-language career query to the agent")
async def agent_query(
    request: AgentQueryRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_agent_query(db=db, user_id=user_id, request=request)


@router.get("/trace/{trace_id}", summary="Retrieve full agent reasoning trace")
async def get_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_get_trace(db=db, user_id=user_id, trace_id=trace_id)


@router.get("/traces", summary="List all agent traces for the authenticated user")
async def list_traces(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    import uuid
    from sqlalchemy import select
    from app.models.trace_models import AgentTrace

    result = await db.execute(
        select(AgentTrace)
        .where(AgentTrace.user_id == uuid.UUID(user_id))
        .order_by(AgentTrace.created_at.desc())
        .limit(50)
    )
    traces = result.scalars().all()
    return {
        "traces": [
            {
                "trace_id": str(t.trace_id),
                "user_query": t.user_query,
                "steps_count": len(t.steps or []),
                "created_at": t.created_at.isoformat(),
            }
            for t in traces
        ]
    }

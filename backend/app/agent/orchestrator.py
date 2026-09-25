"""
Agent orchestrator — Plan-Tool-Observe loop using the google-genai SDK directly.

Uses a manual multi-turn conversation loop instead of LangGraph's tool-calling
node, because LangGraph's Gemini integration requires the old SDK. We implement
the same "Plan → Call Tool → Observe → Repeat" logic explicitly.

Loop cap: MAX_ITERATIONS = 8
All intermediate steps are persisted to the AgentTrace DB record.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tool_registry import TOOL_DEFINITIONS
from app.agent.tools.get_job_details import get_job_details
from app.agent.tools.identify_skill_gaps import identify_skill_gaps
from app.agent.tools.match_resume_to_job import match_resume_to_job
from app.agent.tools.save_feedback import save_feedback
from app.agent.tools.search_jobs import search_jobs
from app.integrations.llm_client import get_client
from app.core.config import settings
from app.models.trace_models import AgentTrace

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 8

SYSTEM_PROMPT = """You are Career Copilot, an expert career advisor AI agent with access to a job database.

Your mission: help the user find roles they genuinely fit, understand their skill gaps, and make informed career decisions.

TOOLS available:
- search_jobs: Find jobs matching keywords. ALWAYS call this first when exploring roles.
- get_job_details: Fetch the full description for a specific job before scoring.
- match_resume_to_job: Score the user's resume against a job. Requires job_id.
- identify_skill_gaps: Aggregate gaps across multiple jobs. Use after matching several roles.
- save_feedback: Record user's interest in a job. Changes future rankings.

RULES:
1. Always search before scoring — never match a job without fetching its details first.
2. Score at least 3 jobs before identifying gaps (if the user asks about gaps).
3. Be specific: cite job titles, companies, and exact skill names. Never vague platitudes.
4. When the user asks a vague question, interpret it helpfully: look for ML/Data/Software roles by default.
5. Final answer must be a clear, structured response that directly answers the user's query.
"""


# ── Tool dispatch ────────────────────────────────────────────────────────────

TOOL_MAP = {
    "search_jobs": search_jobs,
    "get_job_details": get_job_details,
    "match_resume_to_job": match_resume_to_job,
    "identify_skill_gaps": identify_skill_gaps,
    "save_feedback": save_feedback,
}


async def _dispatch_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    db: AsyncSession,
    user_id: str,
) -> Any:
    """Call the matching tool function and return its result."""
    fn = TOOL_MAP.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return await fn(db=db, user_id=user_id, **tool_args)
    except Exception as exc:
        logger.exception("Tool '%s' raised exception", tool_name)
        return {"error": str(exc)}


# ── Main orchestrator ────────────────────────────────────────────────────────

async def run_agent(
    db: AsyncSession,
    user_id: str,
    query: str,
) -> Dict[str, Any]:
    """
    Execute the Plan-Tool-Observe loop for a user query.
    Returns: {trace_id, final_answer, steps}
    """
    client = get_client()
    trace_id = str(uuid.uuid4())
    steps: List[Dict[str, Any]] = []

    # Build initial conversation
    # System prompt is passed via config, not as a history message
    contents: List[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=query)])
    ]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOL_DEFINITIONS,
    )

    final_answer = ""

    for iteration in range(MAX_ITERATIONS):
        t0 = time.monotonic()
        try:
            response = await client.aio.models.generate_content(
                model=settings.LLM_MODEL,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            logger.exception("LLM call failed on iteration %d", iteration)
            final_answer = f"I encountered an error: {exc}"
            break

        elapsed_ms = int((time.monotonic() - t0) * 1000)

        candidate = response.candidates[0] if response.candidates else None
        if candidate is None:
            final_answer = "No response from the model."
            break

        # Append model's response to conversation history
        contents.append(types.Content(role="model", parts=candidate.content.parts))

        # Check for function calls
        function_call_parts = [
            p for p in candidate.content.parts if p.function_call is not None
        ]

        if not function_call_parts:
            # Model produced a text response — this is the final answer
            text_parts = [p.text for p in candidate.content.parts if p.text]
            final_answer = "\n".join(text_parts).strip()
            steps.append({
                "step": iteration,
                "type": "final_answer",
                "content": final_answer,
                "duration_ms": elapsed_ms,
            })
            break

        # Process each function call
        tool_response_parts: List[types.Part] = []

        for fc_part in function_call_parts:
            fc = fc_part.function_call
            tool_name = fc.name
            tool_args = dict(fc.args) if fc.args else {}

            logger.info("Iteration %d — calling tool '%s' with args: %s", iteration, tool_name, tool_args)

            # Execute tool
            t_tool = time.monotonic()
            tool_result = await _dispatch_tool(tool_name, tool_args, db, user_id)
            tool_elapsed = int((time.monotonic() - t_tool) * 1000)

            # Record step
            steps.append({
                "step": iteration,
                "tool": tool_name,
                "input": tool_args,
                "output": _safe_serialize(tool_result),
                "duration_ms": tool_elapsed,
            })

            # Build function response part
            tool_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=tool_name,
                        response={"result": _safe_serialize(tool_result)},
                    )
                )
            )

        # Add all tool results to conversation
        if tool_response_parts:
            contents.append(types.Content(role="user", parts=tool_response_parts))

    else:
        # Hit MAX_ITERATIONS — ask for final summary
        final_answer = await _request_final_answer(client, contents, config)

    # Persist trace to DB
    await _save_trace(db, trace_id, user_id, query, steps, final_answer)

    return {
        "trace_id": trace_id,
        "final_answer": final_answer,
        "steps": steps,
    }


async def _request_final_answer(client: Any, contents: list, config: Any) -> str:
    """After hitting max iterations, request a concise summary."""
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text="Please provide your final answer based on everything you've found so far.")]
        )
    )
    try:
        resp = await client.aio.models.generate_content(
            model=settings.LLM_MODEL,
            contents=contents,
            config=config,
        )
        parts = resp.candidates[0].content.parts if resp.candidates else []
        return " ".join(p.text for p in parts if p.text).strip()
    except Exception:
        return "I've completed my research. Please ask a more specific question for detailed results."


async def _save_trace(
    db: AsyncSession,
    trace_id: str,
    user_id: str,
    query: str,
    steps: List[Dict],
    final_answer: str,
) -> None:
    try:
        trace = AgentTrace(
            trace_id=uuid.UUID(trace_id),
            user_id=uuid.UUID(user_id),
            user_query=query,
            steps=steps,
            final_answer=final_answer,
        )
        db.add(trace)
        await db.commit()
    except Exception:
        logger.exception("Failed to persist agent trace %s", trace_id)
        await db.rollback()


def _safe_serialize(obj: Any) -> Any:
    """Convert arbitrary tool output to JSON-safe format."""
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # Handle Pydantic models, dataclasses, etc.
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return {k: _safe_serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
        if isinstance(obj, list):
            return [_safe_serialize(i) for i in obj]
        return str(obj)

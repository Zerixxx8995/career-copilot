"""
Agent orchestrator — LangGraph-powered Plan → Tool-Call → Observe loop.

Architecture:
- State: messages, tool_results, step_count, trace_steps, final_answer
- Nodes: llm_node (calls Gemini with tools), tool_node (dispatches to Python functions), end_node
- Edges: llm_node → tool_node (if function_call) | end_node (if text answer)
- Hard cap: AGENT_MAX_ITERATIONS iterations to prevent runaway loops

Every tool call and its raw result is appended to trace_steps so the full
reasoning chain is inspectable after the fact via /agent/trace/{trace_id}.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing_extensions import TypedDict

from app.agent.tool_registry import TOOL_DEFINITIONS
from app.agent.tools.get_job_details import get_job_details
from app.agent.tools.identify_skill_gaps import identify_skill_gaps
from app.agent.tools.match_resume_to_job import match_resume_to_job
from app.agent.tools.save_feedback import save_feedback
from app.agent.tools.search_jobs import search_jobs
from app.core.config import settings
from app.models.trace_models import AgentTrace

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Career Copilot, an expert AI career advisor.

You help job-seekers find roles they're genuinely a good fit for, understand
their skill gaps, and get sharper career insights through feedback.

You have access to 5 tools:
- search_jobs: find matching job postings
- get_job_details: retrieve full job info
- match_resume_to_job: score resume vs job (deterministic, not guesswork)
- identify_skill_gaps: aggregate recurring gaps across multiple jobs
- save_feedback: record user feedback to improve future rankings

Guidelines:
- ALWAYS ground your answers in tool results — never fabricate jobs, skills, or scores
- For "find me roles" queries: search → get details → match → synthesise
- For "what am I missing" queries: search → match several → identify_gaps
- Cite specific fit scores and matched/missing requirements in your final answer
- Be direct and constructive — the user wants actionable insight
"""


class AgentState(TypedDict):
    messages: List[Any]
    tool_results: List[Dict[str, Any]]
    step_count: int
    trace_steps: List[Dict[str, Any]]
    final_answer: str
    user_id: str
    db: Any  # AsyncSession (not serialisable, passed through)


def _build_graph(db: AsyncSession, user_id: str) -> Any:
    """Build and compile the LangGraph state graph."""

    model = genai.GenerativeModel(
        model_name=settings.LLM_MODEL,
        tools=TOOL_DEFINITIONS,
        system_instruction=SYSTEM_PROMPT,
    )

    async def llm_node(state: AgentState) -> AgentState:
        """Send current messages to Gemini and get back tool-calls or a final answer."""
        if state["step_count"] >= settings.AGENT_MAX_ITERATIONS:
            return {**state, "final_answer": state.get("final_answer", "Max iterations reached.")}

        chat = model.start_chat(history=state["messages"][:-1])
        last_msg = state["messages"][-1]
        response = await chat.send_message_async(last_msg["parts"])

        # Parse response
        new_messages = list(state["messages"])
        trace_steps = list(state["trace_steps"])

        # Check for function calls
        function_calls = []
        for part in response.parts:
            if hasattr(part, "function_call") and part.function_call.name:
                fc = part.function_call
                function_calls.append({"name": fc.name, "args": dict(fc.args)})

        if function_calls:
            new_messages.append({"role": "model", "parts": response.parts})
            return {
                **state,
                "messages": new_messages,
                "tool_results": function_calls,
                "step_count": state["step_count"] + 1,
                "trace_steps": trace_steps,
            }
        else:
            # Final text answer
            answer = response.text or ""
            trace_steps.append({
                "step": state["step_count"],
                "type": "final_answer",
                "content": answer,
            })
            new_messages.append({"role": "model", "parts": [answer]})
            return {
                **state,
                "messages": new_messages,
                "final_answer": answer,
                "step_count": state["step_count"] + 1,
                "trace_steps": trace_steps,
            }

    async def tool_node(state: AgentState) -> AgentState:
        """Dispatch tool calls to Python functions and collect results."""
        tool_results = state["tool_results"]
        trace_steps = list(state["trace_steps"])
        messages = list(state["messages"])
        function_responses = []

        for call in tool_results:
            name = call["name"]
            args = call["args"]
            start_ms = int(time.time() * 1000)

            try:
                result = await _dispatch_tool(state["db"], state["user_id"], name, args)
            except Exception as exc:
                logger.error("Tool %s failed: %s", name, exc)
                result = {"error": str(exc)}

            duration_ms = int(time.time() * 1000) - start_ms

            trace_steps.append({
                "step": state["step_count"],
                "tool": name,
                "input": args,
                "output": result,
                "duration_ms": duration_ms,
            })

            function_responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=name,
                        response={"result": result},
                    )
                )
            )

        messages.append({"role": "user", "parts": function_responses})
        return {**state, "messages": messages, "trace_steps": trace_steps, "tool_results": []}

    def should_continue(state: AgentState) -> str:
        """Router: continue loop or end."""
        if state.get("final_answer"):
            return END
        if state["step_count"] >= settings.AGENT_MAX_ITERATIONS:
            return END
        if state.get("tool_results"):
            return "tool_node"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("llm_node", llm_node)
    graph.add_node("tool_node", tool_node)
    graph.set_entry_point("llm_node")
    graph.add_conditional_edges("llm_node", should_continue, {"tool_node": "tool_node", END: END})
    graph.add_edge("tool_node", "llm_node")

    return graph.compile()


async def _dispatch_tool(
    db: AsyncSession, user_id: str, name: str, args: Dict[str, Any]
) -> Any:
    """Route a tool name + args to the correct Python function."""
    if name == "search_jobs":
        return await search_jobs(
            db=db,
            user_id=user_id,
            role_keywords=args.get("role_keywords", []),
            location=args.get("location"),
            limit=args.get("limit", 10),
        )
    elif name == "get_job_details":
        return await get_job_details(db=db, job_id=args["job_id"])
    elif name == "match_resume_to_job":
        return await match_resume_to_job(db=db, user_id=user_id, job_id=args["job_id"])
    elif name == "identify_skill_gaps":
        return await identify_skill_gaps(db=db, user_id=user_id, job_ids=args.get("job_ids", []))
    elif name == "save_feedback":
        return await save_feedback(
            db=db, user_id=user_id, job_id=args["job_id"], action=args["action"]
        )
    else:
        raise ValueError(f"Unknown tool: {name}")


async def run_agent(
    db: AsyncSession,
    user_id: str,
    query: str,
) -> Dict[str, Any]:
    """
    Run the full agent loop for a user query.
    Returns { trace_id, final_answer, steps }.
    """
    trace_id = str(uuid.uuid4())
    initial_state: AgentState = {
        "messages": [{"role": "user", "parts": [query]}],
        "tool_results": [],
        "step_count": 0,
        "trace_steps": [],
        "final_answer": "",
        "user_id": user_id,
        "db": db,
    }

    graph = _build_graph(db, user_id)
    final_state = await graph.ainvoke(initial_state)

    # Persist trace
    trace = AgentTrace(
        trace_id=uuid.UUID(trace_id),
        user_id=uuid.UUID(user_id),
        user_query=query,
        steps=final_state["trace_steps"],
        final_answer=final_state.get("final_answer", ""),
    )
    db.add(trace)
    await db.flush()

    logger.info(
        "Agent run complete: trace_id=%s steps=%d",
        trace_id,
        len(final_state["trace_steps"]),
    )

    return {
        "trace_id": trace_id,
        "final_answer": final_state.get("final_answer", ""),
        "steps": final_state["trace_steps"],
    }

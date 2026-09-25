"""
Tool registry — Gemini function-calling schemas using google.genai.types (new SDK).
"""
from __future__ import annotations

from google.genai import types

# ── Helper ──────────────────────────────────────────────────────────────────

def _str_array(description: str) -> types.Schema:
    return types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(type=types.Type.STRING),
        description=description,
    )


def _str(description: str) -> types.Schema:
    return types.Schema(type=types.Type.STRING, description=description)


def _int(description: str) -> types.Schema:
    return types.Schema(type=types.Type.INTEGER, description=description)


# ── Tool definitions ─────────────────────────────────────────────────────────

TOOL_DEFINITIONS: list[types.Tool] = [

    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="search_jobs",
            description=(
                "Search for job postings matching the user's query. Returns a ranked list "
                "of jobs re-ordered by the user's stored preferences. Use this first when "
                "the user wants to find or explore roles."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "role_keywords": _str_array(
                        "Keywords describing the desired role (e.g. 'ML Engineer', 'Python')"
                    ),
                    "location": _str("Preferred location (optional, e.g. 'Mumbai', 'Remote')"),
                    "limit": _int("Max number of results to return (default 10)"),
                },
                required=["role_keywords"],
            ),
        )
    ]),

    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="get_job_details",
            description=(
                "Retrieve the full description and requirements for a specific job. "
                "Also triggers RAG indexing of the posting if not already done. "
                "Call this before scoring to ensure complete data is available."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"job_id": _str("UUID of the job posting")},
                required=["job_id"],
            ),
        )
    ]),

    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="match_resume_to_job",
            description=(
                "Score how well the user's resume matches a specific job. Returns fit score, "
                "matched requirements (with evidence), missing requirements, and a natural-language "
                "explanation. Uses deterministic skill matching + embedding fallback — never guesses."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"job_id": _str("UUID of the job to score against the user's resume")},
                required=["job_id"],
            ),
        )
    ]),

    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="identify_skill_gaps",
            description=(
                "Aggregate recurring skill gaps across multiple job postings. "
                "Use when the user asks about gaps, what they're missing, or wants a "
                "cross-cutting summary across roles. Returns gaps ranked by frequency + "
                "an actionable advisory summary."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"job_ids": _str_array("List of job UUIDs to analyse for gaps")},
                required=["job_ids"],
            ),
        )
    ]),

    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="save_feedback",
            description=(
                "Record user feedback on a job (interested / not_interested / applied). "
                "This immediately updates the user's preference weights, causing future "
                "search_jobs results to shift accordingly."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "job_id": _str("UUID of the job being rated"),
                    "action": _str("One of: 'interested', 'not_interested', 'applied'"),
                },
                required=["job_id", "action"],
            ),
        )
    ]),
]

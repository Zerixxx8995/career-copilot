"""
Tool registry — defines the Gemini function-calling schemas for all 5 agent tools.
"""
from __future__ import annotations

import google.generativeai as genai

TOOL_DEFINITIONS = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="search_jobs",
                description=(
                    "Search for job postings matching the user's query. Returns a ranked list "
                    "of jobs re-ordered by the user's stored preferences. Use this first when "
                    "the user wants to find or explore roles."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "role_keywords": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(type=genai.protos.Type.STRING),
                            description="Keywords describing the desired role (e.g. 'ML Engineer', 'Python')",
                        ),
                        "location": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Preferred location (optional, e.g. 'Mumbai', 'Remote')",
                        ),
                        "limit": genai.protos.Schema(
                            type=genai.protos.Type.INTEGER,
                            description="Max number of results to return (default 10)",
                        ),
                    },
                    required=["role_keywords"],
                ),
            )
        ]
    ),
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="get_job_details",
                description=(
                    "Retrieve the full description and requirements for a specific job. "
                    "Also triggers RAG indexing of the posting if not already done. "
                    "Call this before scoring to ensure complete data is available."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "job_id": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="UUID of the job posting",
                        )
                    },
                    required=["job_id"],
                ),
            )
        ]
    ),
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="match_resume_to_job",
                description=(
                    "Score how well the user's resume matches a specific job. Returns fit score, "
                    "matched requirements (with evidence), missing requirements, and a natural-language "
                    "explanation. Uses deterministic skill matching + embedding fallback — never guesses."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "job_id": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="UUID of the job to score against the user's resume",
                        )
                    },
                    required=["job_id"],
                ),
            )
        ]
    ),
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="identify_skill_gaps",
                description=(
                    "Aggregate recurring skill gaps across multiple job postings. "
                    "Use when the user asks about gaps, what they're missing, or wants a "
                    "cross-cutting summary across roles. Returns gaps ranked by frequency + "
                    "an actionable advisory summary."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "job_ids": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(type=genai.protos.Type.STRING),
                            description="List of job UUIDs to analyse for gaps",
                        )
                    },
                    required=["job_ids"],
                ),
            )
        ]
    ),
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="save_feedback",
                description=(
                    "Record user feedback on a job (interested / not_interested / applied). "
                    "This immediately updates the user's preference weights, causing future "
                    "search_jobs results to shift accordingly."
                ),
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "job_id": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="UUID of the job being rated",
                        ),
                        "action": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="One of: 'interested', 'not_interested', 'applied'",
                        ),
                    },
                    required=["job_id", "action"],
                ),
            )
        ]
    ),
]

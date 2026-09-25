# Career Copilot 🤖

> An **LLM-orchestrated agentic system** that helps job-seekers find roles they're a genuine fit for, understand recurring skill gaps, and get sharper recommendations every time they give feedback.

This is **not a chatbot with a search box**. The identity of the project is the orchestration loop: a Gemini-powered agent that plans, calls tools, reads real results, and adapts — backed by RAG over the resume and job postings, a persistent profile that changes with feedback, and deterministic code (not LLM guesswork) doing the actual scoring.

---

## Architecture

```
Frontend (Next.js + TypeScript)
        │ REST
        ▼
FastAPI Backend
    ├── Routers         → URL mapping only
    ├── Controllers     → Parse request → call service → shape response
    ├── Agent (LangGraph) ─── Plan → Tool-Call → Observe loop (max 8 iterations)
    │       └── Tools:
    │           ├── search_jobs          → keyword filter + preference re-ranking
    │           ├── get_job_details      → full lookup + lazy RAG indexing
    │           ├── match_resume_to_job  → deterministic scoring + LLM explanation
    │           ├── identify_skill_gaps  → aggregation across N jobs
    │           └── save_feedback        → writes weight, shifts future rankings
    ├── Services        → Business logic (matching, ranking, feedback)
    ├── Core            → Pure algorithms (fit_scorer, gap_aggregator, skill_extractor)
    └── Integrations    → Gemini LLM, text-embedding-004, Qdrant
        │
        ├── PostgreSQL (Neon)   → Users, profiles, job postings, match cache, traces
        └── Qdrant              → resume_chunks + job_chunks (RAG)
```

---

## Tech Stack

| Layer         | Technology                    | Why |
|---------------|-------------------------------|-----|
| Backend       | FastAPI (Python 3.11)         | Async, auto OpenAPI docs |
| LLM / Agent   | Gemini 2.0 Flash              | Native function-calling, free tier |
| Agent Loop    | LangGraph                     | Explicit, inspectable state graph |
| Embeddings    | Gemini text-embedding-004     | 768-dim, free tier |
| Vector DB     | Qdrant Cloud                  | Semantic search + filtering |
| Structured DB | PostgreSQL (Neon)             | Profiles, jobs, feedback, traces |
| DB Access     | SQLAlchemy + async + Alembic  | Migration-friendly |
| Resume Parse  | pdfplumber + LLM structuring  | Handles real messy PDFs |
| Frontend      | Next.js 15 + TypeScript       | App Router, clean chat UI |
| Styling       | Tailwind CSS                  | Rapid build |
| CI/CD         | GitHub Actions                | Lint + test on every push |
| Hosting       | Render (backend) + Vercel (frontend) | Free tier |

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- A `.env` file (copy `.env.example` and fill in your keys)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Seed the job postings database
python -m scripts.seed_jobs

# Run the API
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:3000`

---

## Key API Endpoints

### `POST /agent/query`
Submit a natural-language query to the agent.

```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find ML roles in Bengaluru I would be a good fit for and tell me what I am missing"}'
```

Response:
```json
{
  "trace_id": "uuid",
  "answer": "Based on your profile, I found 3 strong matches...",
  "steps_count": 6
}
```

### `POST /feedback`
Record feedback — immediately shifts future search rankings.

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "uuid", "action": "not_interested"}'
```

Response:
```json
{
  "status": "ok",
  "updated_preference_weights": {"ml": 0.8, "frontend": -0.4}
}
```

### `GET /agent/trace/{trace_id}`
Retrieve the full step-by-step agent reasoning chain.

---

## How Fit Scoring Works

1. **Exact match** — normalised string comparison (`"Python 3.x"` ↔ `"Python"`)
2. **Embedding fallback** — cosine similarity (≥0.75) for semantically equivalent terms (`"GPU-accelerated computing"` ↔ `"CUDA"`)
3. **LLM explanation** — writes the natural-language explanation *citing which method matched what* — never invents skills not in the resume

## How Feedback Shifts Rankings

- `interested` → +0.2 weight for that job's role category
- `applied` → +0.3 weight
- `not_interested` → -0.2 weight
- Weights are clamped to `[-1.0, 1.0]`
- `search_jobs` blends keyword relevance with these weights deterministically

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Future Improvements (v2/v3)
- Resume revision suggestions with accept/reject feedback
- Live job API integration (Adzuna / RemoteOK)
- Learning roadmap generation with resource links
- Multi-source job aggregation with deduplication
- Company research tool

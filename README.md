# Career Copilot 🤖

> An **LLM-orchestrated agentic system** that helps job-seekers find roles they're a genuine fit for, understand recurring skill gaps, and get sharper recommendations every time they give feedback.

Career Copilot is **not a chatbot with a search box**. Its core identity is an autonomous **Plan → Tool-Call → Observe → Adapt** orchestration loop backed by RAG over candidate resumes and job postings, persistent feedback-driven profile re-ranking, and deterministic algorithms for fit scoring.

---

## Architecture

```
Frontend (Next.js 16 + TypeScript)
        │ REST (CORS enabled)
        ▼
FastAPI Backend
    ├── Routers         → URL mapping & OpenAPI documentation
    ├── Controllers     → Parse requests → execute service logic → shape responses
    ├── Agent Loop      → Manual Plan → Tool-Call → Observe loop (Max 8 iterations)
    │       └── Tools:
    │           ├── search_jobs          → Keyword filter + preference re-ranking
    │           ├── get_job_details      → Full job lookup
    │           ├── match_resume_to_job  → Deterministic scoring + LLM explanation
    │           ├── identify_skill_gaps  → Skill gap aggregation across matched jobs
    │           └── save_feedback        → Updates category weights & shifts future rankings
    ├── Services        → Business logic (Matching, Ranking, Feedback, Resume Ingestion)
    ├── Core            → Pure algorithms (fit_scorer, gap_aggregator, skill_extractor, security)
    └── Integrations    → google-genai SDK, gemini-embedding-001, Qdrant Cloud
        │
        ├── PostgreSQL (Neon)   → Users, profiles, 50 job postings, match cache, traces
        └── Qdrant Vector DB    → Dual-collection RAG (resume_chunks + job_chunks)
```

---

## Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | FastAPI (Python 3.11/3.13) | Async execution, automatic OpenAPI/Swagger docs |
| **LLM & SDK** | `google-genai` SDK + Gemini 3.x | Multi-model failover (`gemini-3.6-flash`, `gemini-3.5-flash-lite`) |
| **Embeddings** | `gemini-embedding-001` | 3072-dimensional vector embeddings with zero-vector fallbacks |
| **Vector DB** | Qdrant Cloud | Dual-collection semantic search over resume & job chunks |
| **Database** | PostgreSQL (Neon DB) | Async SQLAlchemy + asyncpg, SSL parameter sanitization |
| **Authentication** | JWT + bcrypt | Standardized 72-byte UTF-8 password hashing |
| **Resume Parsing**| `pdfplumber` + LLM Structuring | PDF text extraction with rule-based fallback |
| **Frontend** | Next.js 16 + TypeScript | App Router, interactive agent trace viewer |
| **Styling** | Vanilla CSS + Tailwind v4 | Dark mode glassmorphism UI design system |

---

## Local Setup & Development

### 1. Prerequisites
- **Python**: 3.11+
- **Node.js**: 20+
- **Environment Variables**: Create a `.env` file at the repository root (see `.env.example`).

### 2. Backend Setup
```powershell
cd backend

# Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Seed the 50 job postings into Neon PostgreSQL (Run once)
python -m scripts.seed_jobs

# Start the FastAPI backend server
uvicorn app.main:app --reload --port 8000
```
- **Backend API**: [`http://localhost:8000`](http://localhost:8000)
- **Interactive Swagger Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)

### 3. Frontend Setup
```powershell
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```
- **Web App**: [`http://localhost:3000`](http://localhost:3000)

---

## How It Works

### 1. Deterministic Fit Scoring Pipeline
1. **Exact String Match**: Normalised string comparisons (e.g. `"Python"` ↔ `"Python 3.x"`).
2. **Semantic Vector Fallback**: Cosine similarity (`≥0.75`) using `gemini-embedding-001` vectors for equivalent concepts (e.g. `"GPU Computing"` ↔ `"CUDA"`).
3. **LLM Evidence-Grounded Explanation**: Generates clear natural language summaries citing exact matched and missing requirements.

### 2. Real-Time Feedback Re-Ranking Loop
- **Action Weights**: `saved` (+0.2), `applied` (+0.3), `rejected` (-0.2).
- **Preference Scaling**: Clamped to `[-1.0, 1.0]`. `search_jobs` recalculates `adjusted_score = base_relevance + (weight * 0.3)` in real time based on past user interaction.

### 3. Multi-Model Failover Resilience
- Uses the unified `google-genai` SDK. If a model encounters a 503 high-demand spike or 429 quota limit, the client seamlessly failovers across candidate models (`gemini-3.6-flash` → `gemini-3.5-flash-lite` → `gemini-3.7-flash`).

---

## Testing

Run unit & algorithm tests:
```powershell
cd backend
pytest tests/ -v
```

Run TypeScript type checking:
```powershell
cd frontend
npx tsc --noEmit
```

---

## License
MIT License

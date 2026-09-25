"""
Career Copilot — FastAPI Application Factory.

Wires together middleware, routers, and startup/shutdown lifecycle.
"""
from __future__ import annotations

import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.database import init_db
from app.middleware.error_handler import add_error_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.routers import agent, auth, feedback, jobs, profile, resume

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Factory function — creates and configures the FastAPI application."""

    # ── Sentry ─────────────────────────────────────────────────────────────
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.2,
            environment=settings.APP_ENV,
        )

    app = FastAPI(
        title="Career Copilot API",
        description=(
            "LLM-orchestrated agent that helps job-seekers find roles they're "
            "a genuine fit for, understand skill gaps, and improve with feedback."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ───────────────────────────────────────────────────────────────
    cors_origins = list(settings.CORS_ORIGINS)
    extra_origins = [
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    for origin in extra_origins:
        if origin not in cors_origins:
            cors_origins.append(origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom middleware ──────────────────────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)
    add_error_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────────
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(resume.router, prefix="/resume", tags=["Resume"])
    app.include_router(agent.router, prefix="/agent", tags=["Agent"])
    app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
    app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
    app.include_router(profile.router, prefix="/profile", tags=["Profile"])

    # ── Health ─────────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok", "version": "1.0.0"}

    # ── Lifecycle ──────────────────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("Career Copilot API starting up …")
        await init_db()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("Career Copilot API shutting down …")

    return app


app = create_app()

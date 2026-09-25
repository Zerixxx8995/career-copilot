"""
Seed script — loads job_postings.json into PostgreSQL on first run.
Run: python -m scripts.seed_jobs
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import Base
from app.models.job_models import JobPosting


async def seed():
    data_path = Path(__file__).parent.parent / "data" / "job_postings.json"
    with open(data_path) as f:
        postings = json.load(f)

    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        existing = (await session.execute(select(JobPosting))).scalars().all()
        if existing:
            print(f"Database already has {len(existing)} job postings. Skipping seed.")
            return

        jobs = [JobPosting(**p) for p in postings]
        session.add_all(jobs)
        await session.commit()
        print(f"Seeded {len(jobs)} job postings successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

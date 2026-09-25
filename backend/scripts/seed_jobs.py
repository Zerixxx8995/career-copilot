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

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine
from app.models.job_models import JobPosting


async def seed():
    data_path = Path(__file__).parent.parent / "data" / "job_postings.json"
    with open(data_path) as f:
        postings = json.load(f)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
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

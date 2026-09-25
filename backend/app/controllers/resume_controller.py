"""
Resume controller — parses upload request, calls resume_service, shapes response.
"""
from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

from app.services.resume_service import ingest_resume
from sqlalchemy.ext.asyncio import AsyncSession


async def handle_resume_upload(
    db: AsyncSession,
    user_id: str,
    file: UploadFile,
) -> dict:
    """Validate file type, ingest resume, return structured profile summary."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted.",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File exceeds 10 MB limit.",
        )

    profile = await ingest_resume(
        db=db,
        user_id=user_id,
        file_bytes=content,
        file_name=file.filename,
    )

    return {
        "message": "Resume ingested successfully.",
        "profile": {
            "user_id": str(profile.user_id),
            "target_roles": profile.target_roles,
            "target_locations": profile.target_locations,
            "skills_count": len(profile.skills or []),
            "skills": profile.skills,
        },
    }

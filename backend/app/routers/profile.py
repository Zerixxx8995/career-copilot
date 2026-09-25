"""Profile router — URL mapping only."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.profile_models import CareerProfile

router = APIRouter()


@router.get("", summary="Get the authenticated user's career profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = await db.execute(
        select(CareerProfile).where(CareerProfile.user_id == uuid.UUID(user_id))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found. Upload a resume first.",
        )

    return {
        "user_id": str(profile.user_id),
        "target_roles": profile.target_roles,
        "target_locations": profile.target_locations,
        "skills": profile.skills,
        "preference_weights": profile.preference_weights,
        "resume_file_name": profile.resume_file_name,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }
